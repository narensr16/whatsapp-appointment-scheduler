"""Tests for the /appointments/ REST API endpoints."""
from datetime import datetime, timedelta
from fastapi import status
from app.services.booking_service import BookingService, DoctorNotFoundError
from app.schemas import AppointmentCreate


def test_create_appointment_success(client):
    """Test successful booking returns 201 Created with full booking details."""
    future_slot = (datetime.utcnow() + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
    payload = {
        "user_phone": "+14155552671",
        "doctor_id": 1,
        "slot": future_slot.isoformat()
    }

    response = client.post("/appointments/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] > 0
    assert data["user_phone"] == "+14155552671"
    assert data["doctor_id"] == 1
    assert data["doctor_name"] == "Dr. Alice Smith"
    assert data["status"] == "CONFIRMED"


def test_reject_invalid_phone_number(client):
    """Test validation failure for invalid phone numbers."""
    future_slot = (datetime.utcnow() + timedelta(days=2)).replace(hour=11, minute=0, second=0, microsecond=0)
    payload = {
        "user_phone": "abc-invalid",
        "doctor_id": 1,
        "slot": future_slot.isoformat()
    }
    response = client.post("/appointments/", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reject_unknown_doctor(client):
    """Test booking with non-existent doctor ID returns 404."""
    future_slot = (datetime.utcnow() + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
    payload = {
        "user_phone": "+14155552671",
        "doctor_id": 9999,
        "slot": future_slot.isoformat()
    }
    response = client.post("/appointments/", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not exist" in response.json()["detail"].lower()


def test_reject_past_appointment(client):
    """Test booking an appointment in the past returns 400 Bad Request."""
    past_slot = (datetime.utcnow() - timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    payload = {
        "user_phone": "+14155552671",
        "doctor_id": 1,
        "slot": past_slot.isoformat()
    }
    response = client.post("/appointments/", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "past" in response.json()["detail"].lower()


def test_reject_outside_working_hours(client):
    """Test booking outside working hours (e.g. 7 AM or 8 PM) returns 400."""
    early_slot = (datetime.utcnow() + timedelta(days=2)).replace(hour=7, minute=0, second=0, microsecond=0)
    payload = {
        "user_phone": "+14155552671",
        "doctor_id": 1,
        "slot": early_slot.isoformat()
    }
    response = client.post("/appointments/", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "working hours" in response.json()["detail"].lower()


def test_reject_misaligned_slot_time(client):
    """Test booking misaligned slot (e.g. 10:17 instead of :00 or :30) returns 400."""
    odd_slot = (datetime.utcnow() + timedelta(days=2)).replace(hour=10, minute=17, second=0, microsecond=0)
    payload = {
        "user_phone": "+14155552671",
        "doctor_id": 1,
        "slot": odd_slot.isoformat()
    }
    response = client.post("/appointments/", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "interval" in response.json()["detail"].lower()


def test_reject_slot_with_nonzero_seconds(client):
    """Reject seconds instead of silently rounding a timestamp down."""
    future_slot = (datetime.utcnow() + timedelta(days=2)).replace(hour=10, minute=0, second=45, microsecond=0)
    response = client.post("/appointments/", json={"user_phone": "+14155552671", "doctor_id": 1, "slot": future_slot.isoformat()})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "interval" in response.json()["detail"].lower()


def test_reject_duplicate_booking_conflict(client):
    """Test that booking the same doctor and slot twice returns 409 Conflict."""
    future_slot = (datetime.utcnow() + timedelta(days=3)).replace(hour=14, minute=0, second=0, microsecond=0)
    payload1 = {
        "user_phone": "+14155550001",
        "doctor_id": 1,
        "slot": future_slot.isoformat()
    }
    payload2 = {
        "user_phone": "+14155550002",
        "doctor_id": 1,
        "slot": future_slot.isoformat()
    }

    # First booking succeeds
    res1 = client.post("/appointments/", json=payload1)
    assert res1.status_code == status.HTTP_201_CREATED

    # Second booking for the same slot is rejected with 409
    res2 = client.post("/appointments/", json=payload2)
    assert res2.status_code == status.HTTP_409_CONFLICT
    assert "already booked" in res2.json()["detail"].lower()


def test_two_patients_attempting_same_slot_concurrency(db_session):
    """Simulate concurrent attempts on the same slot at the service layer."""
    future_slot = (datetime.utcnow() + timedelta(days=4)).replace(hour=15, minute=30, second=0, microsecond=0)
    p1 = AppointmentCreate(user_phone="+14155550001", doctor_id=2, slot=future_slot)
    p2 = AppointmentCreate(user_phone="+14155550002", doctor_id=2, slot=future_slot)

    # First succeeds
    appt1 = BookingService.create_appointment(db_session, p1)
    assert appt1.id is not None

    # Second must fail with SlotConflictError
    import pytest
    from app.services.booking_service import SlotConflictError
    with pytest.raises(SlotConflictError):
        BookingService.create_appointment(db_session, p2)


def test_list_and_filter_appointments(client):
    """Test retrieving appointments list with doctor filter."""
    future_slot1 = (datetime.utcnow() + timedelta(days=5)).replace(hour=10, minute=0, second=0, microsecond=0)
    future_slot2 = (datetime.utcnow() + timedelta(days=5)).replace(hour=11, minute=0, second=0, microsecond=0)

    client.post("/appointments/", json={"user_phone": "+14155551111", "doctor_id": 1, "slot": future_slot1.isoformat()})
    client.post("/appointments/", json={"user_phone": "+14155552222", "doctor_id": 2, "slot": future_slot2.isoformat()})

    res = client.get("/appointments/?doctor_id=1")
    assert res.status_code == status.HTTP_200_OK
    items = res.json()
    assert all(item["doctor_id"] == 1 for item in items)


def test_cancellation_and_subsequent_slot_reuse(client):
    """Verify that cancelling an appointment allows that slot to be re-booked."""
    future_slot = (datetime.utcnow() + timedelta(days=6)).replace(hour=10, minute=30, second=0, microsecond=0)
    payload1 = {
        "user_phone": "+14155550001",
        "doctor_id": 1,
        "slot": future_slot.isoformat()
    }

    # 1. First booking succeeds
    res1 = client.post("/appointments/", json=payload1)
    assert res1.status_code == status.HTTP_201_CREATED
    appt1_id = res1.json()["id"]

    # 2. Duplicate booking fails with 409
    payload2 = {
        "user_phone": "+14155550002",
        "doctor_id": 1,
        "slot": future_slot.isoformat()
    }
    res2 = client.post("/appointments/", json=payload2)
    assert res2.status_code == status.HTTP_409_CONFLICT

    # 3. Cancel the first appointment
    cancel_res = client.delete(f"/appointments/{appt1_id}")
    assert cancel_res.status_code == status.HTTP_200_OK

    # 4. Now second patient can book the freed slot
    res3 = client.post("/appointments/", json=payload2)
    assert res3.status_code == status.HTTP_201_CREATED
    data3 = res3.json()
    assert data3["user_phone"] == "+14155550002"
    assert data3["status"] == "CONFIRMED"


def test_database_rollback_on_error(db_session, monkeypatch):
    """Verify that database transaction is safely rolled back when an error occurs during commit."""
    from app.services.booking_service import BookingError
    from app.models import Appointment

    future_slot = (datetime.utcnow() + timedelta(days=6)).replace(hour=14, minute=0, second=0, microsecond=0)
    p = AppointmentCreate(user_phone="+14155558888", doctor_id=1, slot=future_slot)

    # Monkeypatch db_session.commit to simulate database IO failure
    def mock_commit():
        raise RuntimeError("Simulated SQLite disk I/O failure")

    monkeypatch.setattr(db_session, "commit", mock_commit)

    import pytest
    with pytest.raises(BookingError) as exc_info:
        BookingService.create_appointment(db_session, p)

    assert exc_info.value.status_code == 500

    # Ensure no partial uncommitted row remains
    remaining = db_session.query(Appointment).filter(Appointment.user_phone == "+14155558888").first()
    assert remaining is None


def test_reject_phone_abc123(client, db_session):
    """Verify that 'abc123' is rejected with HTTP 422, clear error details, and no DB record created."""
    from app.models import Appointment
    initial_count = db_session.query(Appointment).count()
    future_slot = (datetime.utcnow() + timedelta(days=2)).replace(hour=11, minute=0, second=0, microsecond=0)
    payload = {
        "user_phone": "abc123",
        "doctor_id": 1,
        "slot": future_slot.isoformat()
    }
    response = client.post("/appointments/", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data
    # Check that error specifically mentions letters or alphabetic characters
    assert any("letters" in err.get("msg", "").lower() for err in data["detail"])

    # Ensure no appointment was created in the database
    assert db_session.query(Appointment).count() == initial_count


def test_reject_phone_empty_string(client, db_session):
    """Verify that empty string and whitespace-only phone numbers are rejected with 422 and no DB record."""
    from app.models import Appointment
    initial_count = db_session.query(Appointment).count()
    future_slot = (datetime.utcnow() + timedelta(days=2)).replace(hour=11, minute=30, second=0, microsecond=0)

    for empty_val in ["", "   ", "\t"]:
        payload = {
            "user_phone": empty_val,
            "doctor_id": 1,
            "slot": future_slot.isoformat()
        }
        response = client.post("/appointments/", json=payload)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert any("empty" in err.get("msg", "").lower() or "required" in err.get("msg", "").lower() for err in data["detail"])

    assert db_session.query(Appointment).count() == initial_count


def test_reject_phone_with_invalid_characters(client, db_session):
    """Verify phone numbers with invalid symbols are rejected with HTTP 422."""
    from app.models import Appointment
    initial_count = db_session.query(Appointment).count()
    future_slot = (datetime.utcnow() + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
    payload = {
        "user_phone": "+1415#555*26",
        "doctor_id": 1,
        "slot": future_slot.isoformat()
    }
    response = client.post("/appointments/", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert db_session.query(Appointment).count() == initial_count


def test_create_appointment_international_formats(client):
    """Verify that valid international formats are accepted and properly normalized."""
    test_cases = [
        ("+1 (415) 555-2671", "+14155552671", 10),
        ("+44 20 7946 0919", "+442079460919", 11),
        ("+91 98765 43210", "+919876543210", 14),
        ("14155552671", "14155552671", 15),
    ]

    for raw_phone, expected_normalized, hour in test_cases:
        future_slot = (datetime.utcnow() + timedelta(days=8)).replace(hour=hour, minute=0, second=0, microsecond=0)
        payload = {
            "user_phone": raw_phone,
            "doctor_id": 1,
            "slot": future_slot.isoformat()
        }
        res = client.post("/appointments/", json=payload)
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["user_phone"] == expected_normalized
        assert data["status"] == "CONFIRMED"

