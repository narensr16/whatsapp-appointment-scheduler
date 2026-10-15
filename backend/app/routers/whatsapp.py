"""
WhatsApp Webhook router supporting both Local/Mock simulation and Meta Cloud API webhooks.
Includes natural language parsing, idempotency, clarification responses, and conflict handling with alternative slot suggestions.
"""
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Tuple
import logging
import hashlib
from fastapi import APIRouter, Depends, Request, Response, Header, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import WebhookMessage, Doctor
from app.schemas import WhatsAppResponse, AppointmentCreate, AppointmentResponse
from app.services.message_parser import MessageParser, ParsedBookingRequest
from app.services.booking_service import (
    BookingService,
    DoctorNotFoundError,
    PastSlotError,
    SlotConflictError,
    InvalidSlotTimeError,
    BookingError
)
from app.services.whatsapp_provider import get_whatsapp_provider, MetaWhatsAppCloudProvider
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Webhook"])


@router.get(
    "/",
    summary="Meta WhatsApp Webhook Verification Handshake",
    description="Endpoint for Meta Cloud API webhook subscription challenge."
)
def verify_meta_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge")
):
    """Verifies the webhook token with Meta and echoes back the challenge."""
    if hub_mode == "subscribe" and hub_verify_token == settings.META_VERIFY_TOKEN:
        logger.info("Meta webhook verification succeeded.")
        return Response(content=hub_challenge or "", media_type="text/plain")

    logger.warning("Meta webhook verification failed. Token mismatch or bad mode: token=%s", hub_verify_token)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch.")


@router.post(
    "/",
    response_model=WhatsAppResponse,
    summary="Handle incoming WhatsApp message webhook",
    description="Accepts WhatsApp message (either mock or Meta format), parses intent, executes booking, and responds."
)
async def handle_whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_hub_signature_256: Optional[str] = Header(None)
):
    """
    Main webhook entry point.
    Supports both:
    1. Direct mock JSON payloads: { "sender": "...", "text": "...", "message_id": "..." }
    2. Meta WhatsApp Cloud API webhooks: { "entry": [ { "changes": [ ... ] } ] }
    """
    body_bytes = await request.body()
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload in webhook request.")

    # Meta mode requires a secret and a valid signature; mock mode accepts simulator payloads.
    if settings.WHATSAPP_PROVIDER.strip().lower() == "meta":
        if not settings.META_APP_SECRET:
            raise HTTPException(status_code=503, detail="Meta webhook is not configured securely.")
        if not MetaWhatsAppCloudProvider.verify_webhook_signature(body_bytes, x_hub_signature_256):
            logger.warning("Rejected webhook request due to invalid HMAC signature.")
            raise HTTPException(status_code=401, detail="Invalid webhook signature.")

    # 2. Extract sender, text, message_id
    sender_phone, message_text, message_id = _extract_message_data(payload)

    if not sender_phone or not message_text:
        # Check if it was an empty notification or delivery status update from Meta
        status_label = "status_update" if sender_phone else "ignored"
        reply_label = "Delivery status received." if sender_phone else "No text message to process."
        return WhatsAppResponse(
            status=status_label,
            reply=reply_label,
            message_id=message_id
        )

    # 3. Idempotency Check: prevent duplicate processing of re-delivered webhooks
    if message_id:
        existing_log = db.query(WebhookMessage).filter(WebhookMessage.message_id == message_id).first()
        if existing_log:
            logger.info("Duplicate webhook delivery detected for message_id=%s. Returning cached reply.", message_id)
            return WhatsAppResponse(
                status="duplicate",
                reply=existing_log.response_sent or "This request has already been processed.",
                message_id=message_id
            )

    # 4. Parse natural language request
    parsed = MessageParser.parse_message(message_text)

    # 5. Handle Incomplete or Ambiguous Messages
    if not parsed.is_complete:
        reply_msg = parsed.clarification_prompt or "Could you please specify doctor, date, and time?"
        _record_webhook(db, message_id, sender_phone, message_text, reply_msg)
        _send_outbound_reply(sender_phone, reply_msg)
        return WhatsAppResponse(
            status="clarification_needed",
            reply=reply_msg,
            message_id=message_id
        )

    # 6. Locate Doctor
    doctor = BookingService.find_doctor_by_name_or_alias(db, parsed.doctor_query)
    if not doctor:
        # Provide list of available doctors in the system
        active_doctors = db.query(Doctor).filter(Doctor.is_active.is_(True)).all()
        doc_names = ", ".join([d.name for d in active_doctors]) if active_doctors else "No doctors available"
        reply_msg = (
            f"We could not find a doctor matching '{parsed.doctor_query}'. "
            f"Our available doctors are: {doc_names}. "
            "Please try again, e.g., 'Book Dr. Alice Smith tomorrow at 10 AM'."
        )
        _record_webhook(db, message_id, sender_phone, message_text, reply_msg)
        _send_outbound_reply(sender_phone, reply_msg)
        return WhatsAppResponse(
            status="clarification_needed",
            reply=reply_msg,
            message_id=message_id
        )

    # 7. Attempt Booking
    try:
        appointment_in = AppointmentCreate(
            user_phone=sender_phone,
            doctor_id=doctor.id,
            slot=parsed.slot
        )
        appointment = BookingService.create_appointment(db, appointment_in)

        # Formulate confirmation message
        formatted_slot = appointment.slot.strftime("%A, %d %B %Y at %I:%M %p")
        reply_msg = (
            f"✅ Appointment Confirmed!\n"
            f"Doctor: {doctor.name} ({doctor.specialty})\n"
            f"Time: {formatted_slot}\n"
            f"Booking ID: #{appointment.id}\n"
            f"Patient Phone: {sender_phone}"
        )

        _record_webhook(db, message_id, sender_phone, message_text, reply_msg, appointment.id)
        _send_outbound_reply(sender_phone, reply_msg)

        return WhatsAppResponse(
            status="success",
            reply=reply_msg,
            appointment=AppointmentResponse(
                id=appointment.id,
                user_phone=appointment.user_phone,
                doctor_id=appointment.doctor_id,
                slot=appointment.slot,
                status=appointment.status,
                created_at=appointment.created_at,
                doctor_name=doctor.name
            ),
            message_id=message_id
        )

    except SlotConflictError:
        # Slot is unavailable: generate alternative suggestions
        available = BookingService.get_available_slots(db, doctor.id, parsed.target_date)
        suggested_strings = [s.strftime("%I:%M %p") for s in available[:4]]

        if suggested_strings:
            suggestions_text = ", ".join(suggested_strings)
            reply_msg = (
                f"❌ Sorry, the slot on {parsed.slot.strftime('%d %B at %I:%M %p')} with {doctor.name} is already booked.\n"
                f"Here are available alternative slots for {parsed.target_date.strftime('%d %B')}: {suggestions_text}.\n"
                f"To book one, reply with your preferred time!"
            )
        else:
            reply_msg = (
                f"❌ Sorry, {doctor.name} has no more available slots on {parsed.target_date.strftime('%d %B')}.\n"
                f"Please choose another date or another doctor."
            )

        _record_webhook(db, message_id, sender_phone, message_text, reply_msg)
        _send_outbound_reply(sender_phone, reply_msg)

        return WhatsAppResponse(
            status="conflict",
            reply=reply_msg,
            suggested_slots=suggested_strings,
            message_id=message_id
        )

    except (ValueError, PastSlotError, InvalidSlotTimeError, BookingError) as exc:
        err_msg = exc.message if hasattr(exc, "message") else str(exc)
        reply_msg = f"❌ Booking failed: {err_msg}"
        _record_webhook(db, message_id, sender_phone, message_text, reply_msg)
        _send_outbound_reply(sender_phone, reply_msg)

        return WhatsAppResponse(
            status="error",
            reply=reply_msg,
            message_id=message_id
        )
    except Exception as exc:
        logger.error("Unexpected error in WhatsApp webhook: %s", str(exc), exc_info=True)
        reply_msg = "An unexpected error occurred while processing your booking. Please try again shortly."
        _record_webhook(db, message_id, sender_phone, message_text, reply_msg)
        _send_outbound_reply(sender_phone, reply_msg)

        return WhatsAppResponse(
            status="error",
            reply=reply_msg,
            message_id=message_id
        )


def _extract_message_data(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extracts (sender_phone, message_text, message_id) from either:
    1. Direct mock payload: {"sender": "...", "text": "...", "message_id": "..."}
       or {"from": "...", "body": "..."}
    2. Meta Cloud API payload: entry -> changes -> value -> messages[0]
    """
    # Check Meta Cloud API format
    try:
        if "entry" in payload and isinstance(payload["entry"], list) and len(payload["entry"]) > 0:
            entry = payload["entry"][0]
            changes = entry.get("changes", [])
            if changes and len(changes) > 0:
                value = changes[0].get("value", {})
                
                # 1. Handle delivery status callbacks (sent, delivered, read)
                statuses = value.get("statuses", [])
                if statuses and len(statuses) > 0:
                    status_item = statuses[0]
                    return status_item.get("recipient_id"), None, status_item.get("id")

                # 2. Handle incoming user messages
                messages = value.get("messages", [])
                if messages and len(messages) > 0:
                    msg = messages[0]
                    sender = msg.get("from")
                    msg_id = msg.get("id")
                    text_obj = msg.get("text") or {}
                    text = text_obj.get("body", "") if isinstance(text_obj, dict) else ""
                    return sender, text, msg_id
    except Exception as e:
        logger.debug("Failed parsing as Meta webhook format: %s", str(e))

    # Check direct mock payload format (supporting lower/upper/mixed case keys like From, Body, sender, text, etc.)
    sender = (
        payload.get("From")
        or payload.get("from")
        or payload.get("sender")
        or payload.get("Sender")
        or payload.get("user_phone")
        or payload.get("phone")
    )
    text = (
        payload.get("Body")
        or payload.get("body")
        or payload.get("text")
        or payload.get("Text")
        or payload.get("message")
        or payload.get("Message")
    )
    msg_id = (
        payload.get("MessageSid")
        or payload.get("messageSid")
        or payload.get("message_id")
        or payload.get("Message_Id")
        or payload.get("id")
        or payload.get("Id")
    )

    if not sender or not text:
        # Fallback to case-insensitive lookup across all payload keys
        payload_lower = {str(k).lower(): v for k, v in payload.items()}
        if not sender:
            sender = (
                payload_lower.get("from")
                or payload_lower.get("sender")
                or payload_lower.get("user_phone")
                or payload_lower.get("phone")
            )
        if not text:
            text = (
                payload_lower.get("body")
                or payload_lower.get("text")
                or payload_lower.get("message")
            )
        if not msg_id:
            msg_id = (
                payload_lower.get("messagesid")
                or payload_lower.get("message_id")
                or payload_lower.get("id")
            )

    if sender and text and not msg_id:
        # Generate deterministic message_id if none provided
        msg_id = "msg_" + hashlib.md5(f"{sender}:{text}:{datetime.utcnow().minute}".encode()).hexdigest()[:12]

    return sender, text, msg_id


def _record_webhook(
    db: Session,
    message_id: Optional[str],
    sender: str,
    raw_content: str,
    response_text: str,
    appointment_id: Optional[int] = None
) -> None:
    """Store message in WebhookMessage for audit trail and idempotency."""
    if not message_id:
        return
    try:
        log_entry = WebhookMessage(
            message_id=message_id,
            sender_phone=sender,
            raw_content=raw_content,
            response_sent=response_text,
            appointment_id=appointment_id,
            processed_at=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Could not persist webhook message audit log: %s", str(exc))


def _send_outbound_reply(recipient_phone: str, message: str) -> None:
    """Dispatch outbound message, logging delivery/configuration failures."""
    try:
        result = get_whatsapp_provider().send_message(recipient_phone, message)
        if result.get("delivered") is False:
            logger.error("WhatsApp outbound delivery failed: %s", result.get("error", "unknown error"))
    except Exception as exc:
        logger.error("Error sending outbound message: %s", str(exc), exc_info=True)
