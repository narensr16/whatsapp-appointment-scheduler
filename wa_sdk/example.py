"""
Executable demonstration of using the generated wa_sdk Python client
to interact with the WhatsApp-Based Appointment Scheduling System.
"""
from datetime import datetime, timedelta
import wa_sdk
from wa_sdk.api.health_api import HealthApi
from wa_sdk.api.doctors_api import DoctorsApi
from wa_sdk.api.appointments_api import AppointmentsApi
from wa_sdk.models.appointment_create import AppointmentCreate
from wa_sdk.exceptions import ApiException


def run_sdk_demo(base_url: str = "http://localhost:8000"):
    print("=" * 60)
    print("  WhatsApp Appointment Scheduler - Python SDK Demo")
    print("=" * 60)

    # 1. Configure the API client
    config = wa_sdk.Configuration(host=base_url)
    api_client = wa_sdk.ApiClient(configuration=config)

    # 2. Check API Health
    print(f"\n[1] Checking Health at {base_url}...")
    health_api = HealthApi(api_client)
    try:
        health_status = health_api.check_health_health_get()
        print(f"    Health Status: {health_status.status.upper()}")
        print(f"    Database Status: {health_status.database.upper()}")
        print(f"    App Name: {health_status.app_name}")
    except ApiException as exc:
        print(f"    Health check failed: {exc}")
        return

    # 3. List Doctors
    print("\n[2] Fetching Doctor Roster...")
    doctors_api = DoctorsApi(api_client)
    try:
        doctors = doctors_api.list_doctors_doctors_get()
        print(f"    Found {len(doctors)} active doctors:")
        for doc in doctors:
            print(f"      - ID #{doc.id}: {doc.name} ({doc.specialty})")
    except ApiException as exc:
        print(f"    Failed to list doctors: {exc}")
        return

    # 4. Check available slots for Doctor #1
    if doctors:
        doc_id = doctors[0].id
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"\n[3] Checking available slots for {doctors[0].name} on {tomorrow}...")
        try:
            slot_info = doctors_api.get_doctor_available_slots_doctors_doctor_id_slots_get(
                doctor_id=doc_id,
                target_date=tomorrow
            )
            print(f"    Available slots ({len(slot_info.available_slots)}): {', '.join(slot_info.available_slots[:5])}")
        except ApiException as exc:
            print(f"    Failed to fetch slots: {exc}")

    # 5. Book an Appointment
    print("\n[4] Booking a test appointment via SDK...")
    appointments_api = AppointmentsApi(api_client)
    future_slot = (datetime.utcnow() + timedelta(days=7)).replace(hour=14, minute=0, second=0, microsecond=0)
    new_booking = AppointmentCreate(
        user_phone="+14155554321",
        doctor_id=1,
        slot=future_slot
    )

    try:
        created = appointments_api.create_appointment_appointments_post(appointment_create=new_booking)
        print(f"    Booking Success! Details:")
        print(f"      - Appointment ID: #{created.id}")
        print(f"      - Patient Phone: {created.user_phone}")
        print(f"      - Doctor: {created.doctor_name}")
        print(f"      - Slot Time: {created.slot}")
        print(f"      - Status: {created.status}")
    except ApiException as exc:
        if exc.status == 409:
            print(f"    Slot already booked (409 Conflict): {exc.body}")
        else:
            print(f"    Booking error ({exc.status}): {exc.body}")

    # 6. List all appointments
    print("\n[5] Listing recent appointments...")
    try:
        appts = appointments_api.list_appointments_appointments_get(limit=5)
        print(f"    Retrieved {len(appts)} appointments:")
        for a in appts:
            print(f"      - #{a.id}: {a.user_phone} with {a.doctor_name or a.doctor_id} at {a.slot}")
    except ApiException as exc:
        print(f"    Failed to list appointments: {exc}")

    print("\n" + "=" * 60)
    print("  SDK Demo Completed Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_sdk_demo()
