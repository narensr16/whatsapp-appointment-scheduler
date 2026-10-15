import sys
import os
import socket
import threading
import time
import pytest
from datetime import datetime, timedelta
import httpx
import uvicorn

# Ensure wa_sdk package can be imported even if not installed in editable mode
SDK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "wa_sdk"))
if SDK_DIR not in sys.path and os.path.exists(SDK_DIR):
    sys.path.insert(0, SDK_DIR)

import wa_sdk
from wa_sdk.api.health_api import HealthApi
from wa_sdk.api.doctors_api import DoctorsApi
from wa_sdk.api.appointments_api import AppointmentsApi
from wa_sdk.models.appointment_create import AppointmentCreate
from app.main import app


def test_sdk_imports():
    """Verify that wa_sdk and its modules import successfully."""
    assert wa_sdk.__version__ is not None
    config = wa_sdk.Configuration(host="http://localhost:8000")
    client = wa_sdk.ApiClient(configuration=config)

    health_api = HealthApi(client)
    assert hasattr(health_api, "check_health_health_get")

    doctors_api = DoctorsApi(client)
    assert hasattr(doctors_api, "list_doctors_doctors_get")

    appointments_api = AppointmentsApi(client)
    assert hasattr(appointments_api, "create_appointment_appointments_post")


def test_sdk_model_instantiation():
    """Verify that Pydantic models in wa_sdk can be instantiated with valid data."""
    future_slot = (datetime.utcnow() + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
    req = AppointmentCreate(
        user_phone="+14155552671",
        doctor_id=1,
        slot=future_slot
    )
    assert req.user_phone == "+14155552671"
    assert req.doctor_id == 1
    assert req.slot == future_slot


def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="module")
def live_server_url():
    """Spin up real FastAPI uvicorn server on a free port for end-to-end SDK HTTP testing."""
    from app.database import engine, Base, SessionLocal
    from app.models import Doctor

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(Doctor).count() == 0:
        db.add_all([
            Doctor(id=1, name="Dr. Alice Smith", specialty="Cardiology", phone="+14155550101"),
            Doctor(id=2, name="Dr. Bob Jones", specialty="Pediatrics", phone="+14155550102")
        ])
        db.commit()
    db.close()

    port = find_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"
    # Wait for server readiness
    for _ in range(50):
        try:
            r = httpx.get(f"{url}/health", timeout=1.0)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.1)

    yield url

    server.should_exit = True


def test_sdk_live_http_api_operations(live_server_url):
    """
    Execute real HTTP operations through the generated wa_sdk client against
    a live backend instance, verifying true API connectivity and deserialization.
    """
    config = wa_sdk.Configuration(host=live_server_url)
    api_client = wa_sdk.ApiClient(configuration=config)

    # 1. Health check over HTTP
    health_api = HealthApi(api_client)
    health_res = health_api.check_health_health_get()
    assert health_res.status == "ok"
    assert health_res.database == "connected"

    # 2. List doctors over HTTP
    doctors_api = DoctorsApi(api_client)
    doctors = doctors_api.list_doctors_doctors_get()
    assert len(doctors) > 0
    first_doc_id = doctors[0].id

    # 3. Book appointment over HTTP via wa_sdk client
    appointments_api = AppointmentsApi(api_client)
    future_slot = (datetime.utcnow() + timedelta(days=20)).replace(hour=14, minute=0, second=0, microsecond=0)

    # Ensure slot is clean
    from app.database import SessionLocal
    from app.models import Appointment
    cleanup_db = SessionLocal()
    cleanup_db.query(Appointment).filter(
        Appointment.doctor_id == first_doc_id,
        Appointment.slot == future_slot
    ).delete()
    cleanup_db.commit()
    cleanup_db.close()

    new_booking = AppointmentCreate(
        user_phone="+14155559191",
        doctor_id=first_doc_id,
        slot=future_slot
    )

    created = appointments_api.create_appointment_appointments_post(appointment_create=new_booking)
    assert created.id > 0
    assert created.user_phone == "+14155559191"
    assert created.status == "CONFIRMED"

    # 4. List appointments over HTTP via wa_sdk client
    appointments_list = appointments_api.list_appointments_appointments_get(limit=10)
    assert any(a.user_phone == "+14155559191" for a in appointments_list)

    # Clean up test appointment
    cleanup_db = SessionLocal()
    cleanup_db.query(Appointment).filter(Appointment.user_phone == "+14155559191").delete()
    cleanup_db.commit()
    cleanup_db.close()
