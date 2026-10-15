"""
WhatsApp Provider interface and implementations:
1. MockWhatsAppProvider (for local development and UI simulator)
2. MetaWhatsAppCloudProvider (for live Meta WhatsApp Cloud API)
"""
import hmac
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppProvider(ABC):
    """Abstract base class for WhatsApp delivery providers."""

    @abstractmethod
    def send_message(self, recipient_phone: str, message: str) -> Dict[str, Any]:
        """Send an outbound WhatsApp message to the recipient."""
        pass


class MockWhatsAppProvider(WhatsAppProvider):
    """
    Mock WhatsApp provider for local development, testing, and UI simulator.
    Does not attempt external HTTP calls; logs message and returns delivery simulation.
    """

    def send_message(self, recipient_phone: str, message: str) -> Dict[str, Any]:
        logger.info("[MOCK WHATSAPP] Outbound message to %s:\n%s", recipient_phone, message)
        return {
            "provider": "mock",
            "delivered": True,
            "recipient": recipient_phone,
            "message": message,
            "external_id": f"mock_out_{hash(message) % 10000000}"
        }


class MetaWhatsAppCloudProvider(WhatsAppProvider):
    """
    Meta WhatsApp Cloud API integration using official Graph API endpoints.
    Requires META_WHATSAPP_TOKEN and META_PHONE_NUMBER_ID.
    """

    def __init__(self):
        self.token = settings.META_WHATSAPP_TOKEN
        self.phone_number_id = settings.META_PHONE_NUMBER_ID
        self.api_version = "v19.0"

    def is_configured(self) -> bool:
        return bool(self.token and self.phone_number_id)

    def send_message(self, recipient_phone: str, message: str) -> Dict[str, Any]:
        if not self.is_configured():
            logger.warning("Meta WhatsApp credentials not configured. Falling back to local logging.")
            return {
                "provider": "meta",
                "delivered": False,
                "error": "Meta WhatsApp API credentials missing. Set META_WHATSAPP_TOKEN and META_PHONE_NUMBER_ID."
            }

        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        # Sanitize recipient phone (remove non-digits)
        clean_to = "".join(c for c in recipient_phone if c.isdigit())
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_to,
            "type": "text",
            "text": {"preview_url": False, "body": message}
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                logger.info("Meta WhatsApp message sent successfully: %s", data)
                return {"provider": "meta", "delivered": True, "meta_response": data}
        except Exception as exc:
            logger.error("Failed to send WhatsApp message via Meta Cloud API: %s", str(exc), exc_info=True)
            return {"provider": "meta", "delivered": False, "error": str(exc)}

    @staticmethod
    def verify_webhook_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
        """
        Validate HMAC-SHA256 signature from X-Hub-Signature-256 header.
        """
        if not settings.META_APP_SECRET:
            # Missing secrets must never count as successful verification.
            return False
        if not signature_header or not signature_header.startswith("sha256="):
            return False

        expected_hash = signature_header.split("sha256=")[1].strip()
        calculated_hash = hmac.new(
            key=settings.META_APP_SECRET.encode("utf-8"),
            msg=payload_bytes,
            digestmod=hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(calculated_hash, expected_hash)


def get_whatsapp_provider() -> WhatsAppProvider:
    """Return selected provider; fail closed on invalid Meta configuration."""
    provider = settings.WHATSAPP_PROVIDER.strip().lower()
    if provider == "mock":
        return MockWhatsAppProvider()
    if provider == "meta":
        meta_provider = MetaWhatsAppCloudProvider()
        missing = []
        if not meta_provider.token: missing.append("META_WHATSAPP_TOKEN")
        if not meta_provider.phone_number_id: missing.append("META_PHONE_NUMBER_ID")
        if not settings.META_APP_SECRET: missing.append("META_APP_SECRET")
        if missing:
            raise RuntimeError("WHATSAPP_PROVIDER=meta requires configured values for: " + ", ".join(missing))
        return meta_provider
    raise RuntimeError("WHATSAPP_PROVIDER must be either 'mock' or 'meta'.")
