"""
Dedicated booking service shared by the REST API and WhatsApp webhook.
Enforces all business rules: validation, doctor verification, past-slot rejection,
working-hour limits, slot alignment, and concurrency/uniqueness constraints.
"""
from datetime import datetime, date, time, timedelta
from typing import List, Optional, Tuple
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.models import Appointment, Doctor, WebhookMessage
from app.schemas import AppointmentCreate, AppointmentResponse
from app.config import settings

logger = logging.getLogger(__name__)


class BookingError(Exception):
    """Base exception for booking-related errors."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DoctorNotFoundError(BookingError):
    def __init__(self, message: str = "Doctor not found"):
        super().__init__(message, status_code=404)


class PastSlotError(BookingError):
    def __init__(self, message: str = "Cannot book appointments in the past"):
        super().__init__(message, status_code=400)


class SlotConflictError(BookingError):
    def __init__(self, message: str = "The requested slot is already booked"):
        super().__init__(message, status_code=409)


class InvalidSlotTimeError(BookingError):
    def __init__(self, message: str = "Appointment time is outside working hours or misaligned"):
        super().__init__(message, status_code=400)


class BookingService:
    """Service encapsulating appointment business logic."""

    @staticmethod
    def get_doctor_by_id(db: Session, doctor_id: int) -> Optional[Doctor]:
        """Fetch doctor by primary key ID."""
        return db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.is_active.is_(True)).first()

    @staticmethod
    def find_doctor_by_name_or_alias(db: Session, query: str) -> Optional[Doctor]:
        """
        Fuzzy match doctor by name, alias, or identifier.
        Supports:
        - "Dr. A" -> "Dr. Alice Smith"
        - "Dr. B" -> "Dr. Bob Jones"
        - "Dr. C" -> "Dr. Charlie Brown"
        - Direct name containment
        """
        if not query:
            return None
        cleaned = query.strip().lower()

        # If it's a numeric ID
        if cleaned.isdigit():
            return BookingService.get_doctor_by_id(db, int(cleaned))

        # Check for simple letter aliases (e.g. "Dr. A", "Doctor A", "A")
        alias_map = {
            "a": "alice",
            "dr a": "alice",
            "dr. a": "alice",
            "doctor a": "alice",
            "b": "bob",
            "dr b": "bob",
            "dr. b": "bob",
            "doctor b": "bob",
            "c": "charlie",
            "dr c": "charlie",
            "dr. c": "charlie",
            "doctor c": "charlie"
        }

        search_term = alias_map.get(cleaned, cleaned)
        # Strip "dr." or "dr " if present
        if search_term.startswith("dr."):
            search_term = search_term[3:].strip()
        elif search_term.startswith("dr "):
            search_term = search_term[3:].strip()
        elif search_term.startswith("doctor "):
            search_term = search_term[7:].strip()

        # Query active doctors matching name
        doctors = db.query(Doctor).filter(Doctor.is_active.is_(True)).all()
        for doc in doctors:
            doc_name_lower = doc.name.lower()
            if search_term and (search_term in doc_name_lower or doc_name_lower in search_term):
                return doc

        return None

    @staticmethod
    def validate_slot_rules(slot: datetime) -> None:
        """
        Validate business rules for slot time:
        1. Not in the past.
        2. Within working hours (default 09:00 - 17:00).
        3. Aligned with slot duration (e.g. minutes % 30 == 0, seconds == 0).
        """
        now = datetime.utcnow()
        if slot <= now:
            raise PastSlotError("Appointment slot cannot be in the past.")

        # Check minutes alignment
        interval = settings.SLOT_DURATION_MINUTES
        if slot.minute % interval != 0 or slot.second != 0 or slot.microsecond != 0:
            raise InvalidSlotTimeError(
                f"Appointment slot must align with {interval}-minute intervals (e.g., :00 or :{interval:02d})."
            )

        # Check working hours
        hour = slot.hour
        # Last appointment ends at WORK_END_HOUR, so start time must be < WORK_END_HOUR
        if hour < settings.WORK_START_HOUR or hour >= settings.WORK_END_HOUR:
            raise InvalidSlotTimeError(
                f"Appointments can only be booked during working hours: "
                f"{settings.WORK_START_HOUR:02d}:00 to {settings.WORK_END_HOUR:02d}:00."
            )

    @staticmethod
    def is_slot_available(db: Session, doctor_id: int, slot: datetime) -> bool:
        """Check if doctor has an existing confirmed appointment for the slot."""
        existing = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.slot == slot,
            Appointment.status == "CONFIRMED"
        ).first()
        return existing is None

    @staticmethod
    def get_available_slots(db: Session, doctor_id: int, target_date: date) -> List[datetime]:
        """
        Generate and return list of available datetime slots for a given doctor on a given date.
        """
        now = datetime.utcnow()
        interval = timedelta(minutes=settings.SLOT_DURATION_MINUTES)
        start_dt = datetime.combine(target_date, time(hour=settings.WORK_START_HOUR, minute=0))
        end_dt = datetime.combine(target_date, time(hour=settings.WORK_END_HOUR, minute=0))

        # Query existing appointments for that doctor on that day
        day_start = datetime.combine(target_date, time.min)
        day_end = datetime.combine(target_date, time.max)
        booked_appointments = db.query(Appointment.slot).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.slot >= day_start,
            Appointment.slot <= day_end,
            Appointment.status == "CONFIRMED"
        ).all()
        booked_slots = {appt[0] for appt in booked_appointments}

        available = []
        curr = start_dt
        while curr < end_dt:
            if curr > now and curr not in booked_slots:
                available.append(curr)
            curr += interval

        return available

    @staticmethod
    def create_appointment(
        db: Session,
        appointment_in: AppointmentCreate
    ) -> Appointment:
        """
        Atomically create a confirmed appointment.
        Validates doctor existence, past dates, slot rules, and catches concurrency conflicts.
        """
        # 1. Verify doctor exists and is active
        doctor = BookingService.get_doctor_by_id(db, appointment_in.doctor_id)
        if not doctor:
            raise DoctorNotFoundError(f"Doctor with ID {appointment_in.doctor_id} does not exist.")

        # Preserve precision so invalid seconds/microseconds are rejected, not rounded.
        slot = appointment_in.slot

        # 3. Validate slot rules
        BookingService.validate_slot_rules(slot)

        # 4. Check slot availability
        if not BookingService.is_slot_available(db, appointment_in.doctor_id, slot):
            raise SlotConflictError(
                f"Doctor {doctor.name} is already booked at {slot.strftime('%Y-%m-%d %I:%M %p')}."
            )

        # 5. Create or reactivate appointment with transaction & DB constraint safety
        try:
            # Check if there is a previously cancelled appointment for this slot to reuse
            cancelled_appt = db.query(Appointment).filter(
                Appointment.doctor_id == appointment_in.doctor_id,
                Appointment.slot == slot,
                Appointment.status == "CANCELLED"
            ).first()

            if cancelled_appt:
                cancelled_appt.user_phone = appointment_in.user_phone
                cancelled_appt.status = "CONFIRMED"
                cancelled_appt.created_at = datetime.utcnow()
                db.commit()
                db.refresh(cancelled_appt)
                logger.info("Reactivated cancelled appointment slot: ID=%d, Doctor=%s, Slot=%s",
                            cancelled_appt.id, doctor.name, slot)
                return cancelled_appt

            appointment = Appointment(
                user_phone=appointment_in.user_phone,
                doctor_id=appointment_in.doctor_id,
                slot=slot,
                status="CONFIRMED",
                created_at=datetime.utcnow()
            )
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            logger.info("Appointment created successfully: ID=%d, Doctor=%s, Slot=%s",
                        appointment.id, doctor.name, slot)
            return appointment
        except IntegrityError as exc:
            db.rollback()
            logger.warning("Concurrency conflict or unique constraint violated for doctor %d slot %s: %s",
                           appointment_in.doctor_id, slot, str(exc))
            raise SlotConflictError(
                f"Slot {slot.strftime('%Y-%m-%d %I:%M %p')} was just booked by another patient."
            )
        except Exception as exc:
            db.rollback()
            logger.error("Unexpected error saving appointment: %s", str(exc), exc_info=True)
            raise BookingError(f"Database error while booking appointment: {str(exc)}", status_code=500)

    @staticmethod
    def list_appointments(
        db: Session,
        doctor_id: Optional[int] = None,
        user_phone: Optional[str] = None,
        date_filter: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Appointment]:
        """Fetch list of appointments with optional filtering."""
        query = db.query(Appointment)
        if doctor_id:
            query = query.filter(Appointment.doctor_id == doctor_id)
        if user_phone:
            query = query.filter(Appointment.user_phone == user_phone)
        if date_filter:
            start_dt = datetime.combine(date_filter, time.min)
            end_dt = datetime.combine(date_filter, time.max)
            query = query.filter(Appointment.slot >= start_dt, Appointment.slot <= end_dt)

        return query.order_by(Appointment.slot.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def cancel_appointment(db: Session, appointment_id: int) -> bool:
        """Cancel an appointment by ID."""
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            return False
        appt.status = "CANCELLED"
        db.commit()
        return True
