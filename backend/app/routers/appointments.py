"""Appointment REST API endpoints."""
from datetime import date
from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas import AppointmentCreate, AppointmentResponse, ErrorResponse
from app.services.booking_service import (
    BookingService,
    DoctorNotFoundError,
    PastSlotError,
    SlotConflictError,
    InvalidSlotTimeError,
    BookingError
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new doctor appointment",
    description="Validates doctor availability, working hours, and bookable slot, then creates a confirmed appointment.",
    responses={
        201: {"description": "Appointment successfully booked."},
        400: {"model": ErrorResponse, "description": "Invalid input, past slot, or invalid slot timing."},
        404: {"model": ErrorResponse, "description": "Doctor not found."},
        409: {"model": ErrorResponse, "description": "Slot conflict - appointment slot already booked."},
        500: {"model": ErrorResponse, "description": "Internal server error."}
    }
)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db)
):
    """
    Accepts validated booking request:
    - user_phone: patient phone number
    - doctor_id: ID of the doctor
    - slot: requested date and time
    """
    try:
        appointment = BookingService.create_appointment(db, payload)
        doctor = BookingService.get_doctor_by_id(db, appointment.doctor_id)
        doctor_name = doctor.name if doctor else None

        return AppointmentResponse(
            id=appointment.id,
            user_phone=appointment.user_phone,
            doctor_id=appointment.doctor_id,
            slot=appointment.slot,
            status=appointment.status,
            created_at=appointment.created_at,
            doctor_name=doctor_name
        )
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except PastSlotError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    except SlotConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    except InvalidSlotTimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    except BookingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        logger.error("Unhandled exception creating appointment: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while booking the appointment."
        )


@router.get(
    "/",
    response_model=List[AppointmentResponse],
    summary="List appointments",
    description="Retrieve appointments filtered by doctor, patient phone number, or date."
)
def list_appointments(
    doctor_id: Optional[int] = Query(None, description="Filter by doctor ID"),
    user_phone: Optional[str] = Query(None, description="Filter by patient phone number"),
    appointment_date: Optional[date] = Query(None, description="Filter by appointment date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List appointments with optional query parameters."""
    appointments = BookingService.list_appointments(
        db,
        doctor_id=doctor_id,
        user_phone=user_phone,
        date_filter=appointment_date,
        skip=skip,
        limit=limit
    )

    result = []
    for appt in appointments:
        result.append(
            AppointmentResponse(
                id=appt.id,
                user_phone=appt.user_phone,
                doctor_id=appt.doctor_id,
                slot=appt.slot,
                status=appt.status,
                created_at=appt.created_at,
                doctor_name=appt.doctor.name if appt.doctor else None
            )
        )
    return result


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Get appointment by ID"
)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a single appointment by its ID."""
    appt = db.query(BookingService.get_doctor_by_id(db, 1)).first() # placeholder check
    from app.models import Appointment
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")
    return AppointmentResponse(
        id=appointment.id,
        user_phone=appointment.user_phone,
        doctor_id=appointment.doctor_id,
        slot=appointment.slot,
        status=appointment.status,
        created_at=appointment.created_at,
        doctor_name=appointment.doctor.name if appointment.doctor else None
    )


@router.delete(
    "/{appointment_id}",
    summary="Cancel an appointment"
)
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """Mark an appointment as cancelled."""
    success = BookingService.cancel_appointment(db, appointment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")
    return {"status": "success", "message": f"Appointment {appointment_id} cancelled."}
