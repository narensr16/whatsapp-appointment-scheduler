"""SQLAlchemy models for Doctors, Appointments, and Webhook Audit."""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    Index,
    Text
)
from sqlalchemy.orm import relationship
from app.database import Base


class Doctor(Base):
    """Doctor model representing medical practitioners."""
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    specialty = Column(String(100), nullable=True, default="General Physician")
    phone = Column(String(32), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    appointments = relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Doctor(id={self.id}, name='{self.name}', specialty='{self.specialty}')>"


class Appointment(Base):
    """
    Appointment model adhering to the required challenge fields:
    - id
    - user_phone
    - doctor_id
    - slot
    Table name: whatsapp_appointments (per Challenge specification)
    Enforces uniqueness on (doctor_id, slot) at the database level.
    """
    __tablename__ = "whatsapp_appointments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_phone = Column(String(32), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    slot = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="CONFIRMED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    doctor = relationship("Doctor", back_populates="appointments")

    __table_args__ = (
        UniqueConstraint("doctor_id", "slot", name="uq_doctor_slot"),
        Index("idx_doctor_slot", "doctor_id", "slot"),
    )

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, user_phone='{self.user_phone}', doctor_id={self.doctor_id}, slot='{self.slot}')>"


class WebhookMessage(Base):
    """Audit and idempotency log for incoming WhatsApp webhook messages."""
    __tablename__ = "webhook_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(String(128), unique=True, index=True, nullable=False)
    sender_phone = Column(String(32), nullable=False, index=True)
    raw_content = Column(Text, nullable=True)
    response_sent = Column(Text, nullable=True)
    appointment_id = Column(Integer, ForeignKey("whatsapp_appointments.id", ondelete="SET NULL"), nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<WebhookMessage(id={self.id}, message_id='{self.message_id}', sender='{self.sender_phone}')>"
