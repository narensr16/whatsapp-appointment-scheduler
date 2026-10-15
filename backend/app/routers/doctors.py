"""Doctor management and slot discovery router."""
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Doctor
from app.schemas import DoctorCreate, DoctorResponse, DoctorSlotsResponse
from app.services.booking_service import BookingService

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get(
    "/",
    response_model=List[DoctorResponse],
    summary="List all active doctors"
)
def list_doctors(db: Session = Depends(get_db)):
    """Fetch all doctors available for appointments."""
    doctors = db.query(Doctor).filter(Doctor.is_active.is_(True)).order_by(Doctor.id).all()
    return doctors


@router.post(
    "/",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new doctor"
)
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)):
    """Add a new doctor to the clinic roster."""
    doctor = Doctor(
        name=payload.name.strip(),
        specialty=payload.specialty.strip() if payload.specialty else "General Physician",
        phone=payload.phone,
        is_active=payload.is_active,
        created_at=datetime.utcnow()
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.get(
    "/{doctor_id}/slots",
    response_model=DoctorSlotsResponse,
    summary="Get available slots for a doctor on a specific date"
)
def get_doctor_available_slots(
    doctor_id: int,
    target_date: Optional[date] = Query(None, description="Date to check (defaults to today)"),
    db: Session = Depends(get_db)
):
    """Returns available 30-minute booking slots for a doctor on the requested date."""
    doctor = BookingService.get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found.")

    query_date = target_date or date.today()
    slots = BookingService.get_available_slots(db, doctor_id, query_date)
    formatted_slots = [s.strftime("%I:%M %p") for s in slots]

    return DoctorSlotsResponse(
        doctor_id=doctor.id,
        doctor_name=doctor.name,
        date=query_date.isoformat(),
        available_slots=formatted_slots
    )
