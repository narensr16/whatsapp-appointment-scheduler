"""Pydantic schemas for request validation and response serialization."""
import re
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class DoctorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Dr. Alice Smith"])
    specialty: Optional[str] = Field("General Physician", max_length=100, examples=["Cardiologist"])
    phone: Optional[str] = Field(None, max_length=32, examples=["+1234567890"])
    is_active: bool = Field(True, examples=[True])


class DoctorCreate(DoctorBase):
    pass


class DoctorResponse(DoctorBase):
    id: int = Field(..., examples=[1])
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentCreate(BaseModel):
    """
    Validated request schema for creating an appointment:
    - user_phone: international or local phone number (normalized to digits with optional leading '+')
    - doctor_id: positive integer ID of active doctor
    - slot: datetime representing booking slot
    """
    user_phone: str = Field(..., max_length=32, examples=["+14155552671"])
    doctor_id: int = Field(..., gt=0, examples=[1])
    slot: datetime = Field(..., examples=["2026-10-15T10:00:00"])

    @field_validator("user_phone", mode="before")
    @classmethod
    def validate_phone(cls, v: Any) -> str:
        if v is None or not isinstance(v, str) or not v.strip():
            raise ValueError("Phone number is required and cannot be empty.")
        raw = v.strip()
        if re.search(r"[a-zA-Z]", raw):
            raise ValueError("Phone number cannot contain letters or alphabetic characters.")
        cleaned = re.sub(r"[\s\-\(\)\.]", "", raw)
        if not re.match(r"^\+?[0-9]{7,20}$", cleaned):
            raise ValueError("Phone number must contain between 7 and 20 digits, optionally starting with '+'.")
        return cleaned


class AppointmentResponse(BaseModel):
    """Success response returned upon booking creation."""
    id: int = Field(..., examples=[1])
    user_phone: str = Field(..., examples=["+14155552671"])
    doctor_id: int = Field(..., examples=[1])
    slot: datetime = Field(..., examples=["2026-10-15T10:00:00"])
    status: str = Field("CONFIRMED", examples=["CONFIRMED"])
    created_at: datetime
    doctor_name: Optional[str] = Field(None, examples=["Dr. Alice Smith"])

    model_config = ConfigDict(from_attributes=True)


class AvailableSlotResponse(BaseModel):
    """Available slot details for a doctor."""
    slot: datetime = Field(..., examples=["2026-10-15T10:00:00"])
    formatted_time: str = Field(..., examples=["10:00 AM"])
    is_available: bool = Field(..., examples=[True])


class DoctorSlotsResponse(BaseModel):
    doctor_id: int
    doctor_name: str
    date: str
    available_slots: List[str]


class MockWhatsAppIncoming(BaseModel):
    """Local/mock WhatsApp message payload."""
    sender: str = Field(..., max_length=32, examples=["+14155552671"])
    text: str = Field(..., min_length=1, max_length=1000, examples=["Book appointment with Dr. A at 10 AM tomorrow"])
    message_id: Optional[str] = Field(None, examples=["msg_123456789"])

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Extract case-insensitively or check common aliases
            if "sender" not in data or not data["sender"]:
                for key in ("From", "from", "user_phone", "sender_phone", "phone"):
                    if key in data and data[key]:
                        data["sender"] = data[key]
                        break
            if "text" not in data or not data["text"]:
                for key in ("Body", "body", "message", "text_body"):
                    if key in data and data[key]:
                        data["text"] = data[key]
                        break
            if "message_id" not in data or not data["message_id"]:
                for key in ("MessageSid", "messageSid", "id", "sms_message_sid"):
                    if key in data and data[key]:
                        data["message_id"] = data[key]
                        break
        return data

    @field_validator("sender", mode="before")
    @classmethod
    def validate_sender(cls, v: Any) -> str:
        if v is None or not isinstance(v, str) or not v.strip():
            raise ValueError("Sender phone number is required and cannot be empty.")
        raw = v.strip()
        if re.search(r"[a-zA-Z]", raw):
            raise ValueError("Sender phone number cannot contain letters or alphabetic characters.")
        cleaned = re.sub(r"[\s\-\(\)\.]", "", raw)
        if not re.match(r"^\+?[0-9]{7,20}$", cleaned):
            raise ValueError("Sender phone number must contain between 7 and 20 digits, optionally starting with '+'.")
        return cleaned


class WhatsAppResponse(BaseModel):
    """Standardized response from the WhatsApp webhook endpoint."""
    status: str = Field(..., examples=["success"])
    reply: str = Field(..., examples=["Your appointment with Dr. Alice Smith is confirmed for tomorrow at 10:00 AM."])
    appointment: Optional[AppointmentResponse] = None
    suggested_slots: Optional[List[str]] = None
    message_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = Field("ok", examples=["ok"])
    app_name: str = Field(..., examples=["WhatsApp Appointment Scheduler"])
    version: str = Field(..., examples=["1.0.0"])
    database: str = Field("connected", examples=["connected"])
    timestamp: datetime


class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["The requested slot is already booked."])
