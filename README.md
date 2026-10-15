# WhatsApp-Based Appointment Scheduling System

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg)](https://www.sqlite.org)
[![Alembic](https://img.shields.io/badge/Alembic-Migrations-red.svg)](https://alembic.sqlalchemy.org)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![OpenAPI Generator](https://img.shields.io/badge/OpenAPI-Python_SDK-brightgreen.svg)](https://openapi-generator.tech)
[![Tests: 36 Passed](https://img.shields.io/badge/Tests-36%20Passed-success.svg)](backend/tests/)

A complete, production-quality full-stack system for automated medical appointment scheduling via natural-language WhatsApp messages and REST APIs. Built with FastAPI, SQLite, SQLAlchemy, Alembic, ReactJS, and an OpenAPI-generated Python client SDK.

---

## 📑 Table of Contents

1. [Architectural Overview](#architectural-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Windows 11)](#quick-start-windows-11)
4. [Project Structure](#project-structure)
5. [Configuration & Environment Variables](#configuration--environment-variables)
6. [Database Management & Migrations](#database-management--migrations)
7. [API Endpoints & Swagger UI](#api-endpoints--swagger-ui)
8. [Natural Language WhatsApp Webhook](#natural-language-whatsapp-webhook)
9. [Meta WhatsApp Cloud API Integration (Live Mode)](#meta-whatsapp-cloud-api-integration-live-mode)
10. [React Web Application](#react-web-application)
11. [Generated Python Client SDK (`wa_sdk`)](#generated-python-client-sdk-wa_sdk)
12. [Automated Testing](#automated-testing)
13. [Troubleshooting Guide](#troubleshooting-guide)
14. [Business Rules & Assumptions](#business-rules--assumptions)

---

## 1. Architectural Overview

```
                      ┌───────────────────────────────────────────────┐
                      │             Incoming Booking Request          │
                      └───────────────────────┬───────────────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      │                                               │
                      ▼                                               ▼
         ┌─────────────────────────┐                     ┌─────────────────────────┐
         │  REST API Client / App  │                     │  WhatsApp / Webhook UI  │
         │ (POST /appointments/)   │                     │    (POST /whatsapp/)    │
         └────────────┬────────────┘                     └────────────┬────────────┘
                      │                                               │
                      │ Validated Schema                              │ Natural Language Parsing
                      │                                               │ (Doctor, Date, Time, Intent)
                      │                                               ▼
                      │                                  ┌─────────────────────────┐
                      │                                  │     MessageParser       │
                      │                                  └────────────┬────────────┘
                      │                                               │ Normalized Request
                      ▼                                               ▼
         ┌─────────────────────────────────────────────────────────────────────────┐
         │                          BookingService                                 │
         │  - Doctor verification & working hours check (09:00 - 17:00)            │
         │  - Past date rejection & 30-minute slot interval alignment              │
         │  - Slot availability query & conflict detection (409)                   │
         │  - Atomic SQLite transaction & DB UniqueConstraint(doctor_id, slot)     │
         │  - Slot reuse for cancelled appointments                                │
         │  - Suggest alternative slots on conflict                                │
         └────────────────────────────────────┬────────────────────────────────────┘
                                              │
                                              ▼
         ┌─────────────────────────────────────────────────────────────────────────┐
         │                              SQLite DB                                  │
         │  - doctors (id, name, specialty, phone, is_active)                      │
         │  - whatsapp_appointments (id, user_phone, doctor_id, slot, status)       │
         │  - webhook_messages (message_id, sender_phone, raw, response_sent)      │
         └─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites

| Tool | Minimum Version | Verified Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Python** | 3.10+ | 3.11.9 | FastAPI backend & test runner |
| **Node.js** | 18+ | 24.20.0 (LTS) | React frontend & npm tooling |
| **npm** | 9+ | 11.19.0 | Frontend package management |
| **Java (JRE/JDK)** | 11+ | Temurin 17.0.20 | OpenAPI Generator CLI |
| **OS** | Windows 10/11 | Windows 11 | Local native execution environment |

> [!IMPORTANT]
> **Docker is strictly not used.** The entire system runs natively on Windows.

---

## 3. Quick Start (Windows 11)

### Option A: One-Click Automated Setup

From the repository root directory in Windows CMD or PowerShell:

```bat
:: 1. Run the automated developer setup
setupdev.bat

:: 2. Launch backend and frontend development servers
runapplication.bat
```

`setupdev.bat` automatically:
1. Validates Python, Node.js, and npm.
2. Creates the Python virtual environment in `.venv/`.
3. Installs backend dependencies from `backend/requirements.txt`.
4. Copies `.env.example` to `.env` (preserving any existing `.env`).
5. Applies Alembic database migrations (`alembic upgrade head`).
6. Seeds initial test doctors from `backend/seed_data.sql`.
7. Installs frontend dependencies with `npm install`.

`runapplication.bat` launches:
- **FastAPI backend**: `http://localhost:8000` (Swagger UI at `http://localhost:8000/docs`)
- **React frontend**: `http://localhost:5173`

---

### Option B: Manual Step-by-Step Setup

If you prefer executing each step manually:

#### 1. Configure Python Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### 2. Configure Environment Variables
```powershell
copy .env.example .env
```

#### 3. Run Alembic Database Migrations & Seed
```powershell
cd backend
..\.venv\Scripts\alembic.exe upgrade head
..\.venv\Scripts\python.exe -c "import sqlite3; conn = sqlite3.connect('appointments.db'); conn.executescript(open('seed_data.sql').read()); conn.commit(); print('Seeded!')"
cd ..
```

#### 4. Install & Launch Frontend
```powershell
cd frontend
npm install
npm run dev
```

#### 5. Launch Backend
In a separate terminal:
```powershell
cd backend
..\.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 4. Project Structure

```
whatsapp-appointment-scheduler/
├── .env.example                # Sample environment variables
├── .gitignore                  # Git exclusions (DBs, venvs, node_modules)
├── README.md                   # This documentation
├── openapi.json                # Exported OpenAPI 3.1 specification
├── runapplication.bat          # Script to launch backend and frontend
├── setupdev.bat                # Script for 1-click dev setup and migration
├── backend/
│   ├── alembic.ini             # Alembic migration configuration
│   ├── appointments.db         # Local SQLite database (generated)
│   ├── requirements.txt        # Backend Python dependencies
│   ├── seed_data.sql           # Initial SQL seed data for doctors & bookings
│   ├── alembic/
│   │   ├── env.py              # Alembic environment with model metadata
│   │   ├── script.py.mako      # Alembic migration script template
│   │   └── versions/
│   │       └── 001_initial_schema.py # Initial DDL schema migration
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic BaseSettings configuration
│   │   ├── database.py         # SQLAlchemy engine and session setup
│   │   ├── dependencies.py     # FastAPI get_db dependency injection
│   │   ├── main.py             # FastAPI entrypoint, CORS, startup seeding
│   │   ├── models.py           # SQLAlchemy models: Doctor, Appointment, WebhookMessage
│   │   ├── schemas.py          # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── appointments.py # REST endpoints: POST, GET, DELETE /appointments/
│   │   │   ├── doctors.py      # Endpoints: GET /doctors/, GET /doctors/{id}/slots
│   │   │   ├── health.py       # Endpoint: GET /health
│   │   │   └── whatsapp.py     # Webhook: POST /whatsapp/, GET /whatsapp/
│   │   └── services/
│   │       ├── booking_service.py   # Core booking logic, availability & transactions
│   │       ├── message_parser.py    # Natural-language regex & date/time extractor
│   │       └── whatsapp_provider.py # Mock & Meta WhatsApp Cloud API providers
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py         # Test fixtures & SQLite in-memory DB isolation
│       ├── test_appointments.py# REST API booking & conflict test suite
│       ├── test_health.py      # Health & liveness probe tests
│       ├── test_parser.py      # Natural language parser test cases
│       ├── test_sdk.py         # wa_sdk client validation tests
│       └── test_whatsapp.py    # WhatsApp webhook & Meta format test suite
├── frontend/
│   ├── index.html              # HTML5 entrypoint
│   ├── package.json            # Vite, React, Axios, Lucide dependencies
│   ├── vite.config.js          # Vite dev server configuration
│   └── src/
│       ├── App.jsx             # Main dashboard layout (Chat + Tabs)
│       ├── api.js              # Axios HTTP client configuration
│       ├── index.css           # Modern design system & WhatsApp styling
│       ├── main.jsx            # React root renderer
│       └── components/
│           ├── AppointmentsList.jsx  # Live appointments table & cancel button
│           ├── DirectBookingForm.jsx # Direct REST API booking form
│           ├── DoctorRoster.jsx      # Doctor staff & slot inspector
│           ├── Navbar.jsx            # Header & live backend health badge
│           └── WhatsAppChat.jsx      # Interactive WhatsApp simulator phone
├── scripts/
│   └── generate_sdk.bat        # Batch script to regenerate Python SDK
└── wa_sdk/                     # Generated Python Client SDK
    ├── example.py              # Executable demonstration script
    ├── pyproject.toml          # SDK package definition
    ├── setup.py                # Setuptools installation script
    ├── wa_sdk/                 # Generated Python modules
    └── docs/                   # Generated SDK documentation
```

---

## 5. Configuration & Environment Variables

All settings can be customized in `.env` (inherited via `pydantic-settings`):

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite:///./appointments.db` | SQLAlchemy database connection URI |
| `APP_TIMEZONE` | `UTC` | Clinic reference timezone |
| `SLOT_DURATION_MINUTES` | `30` | Duration of each appointment slot |
| `WORK_START_HOUR` | `9` | Clinic opening hour (09:00 AM) |
| `WORK_END_HOUR` | `17` | Clinic closing hour (05:00 PM) |
| `WHATSAPP_PROVIDER` | `mock` | Messaging mode (`mock` or `meta`) |
| `META_WHATSAPP_TOKEN` | `""` | Meta System User / Access Token |
| `META_PHONE_NUMBER_ID`| `""` | Meta Cloud API Phone Number ID |
| `META_VERIFY_TOKEN` | `appointment_scheduler_verify_token` | Webhook verification challenge token |
| `META_APP_SECRET` | `""` | Meta App Secret for HMAC-SHA256 signature validation |
| `CORS_ORIGINS` | `["http://localhost:5173", "http://localhost:5174", ...]` | Allowed browser origins (supports ports 5173, 5174, 5175, 3000) |

---

## 6. Database Management & Migrations

The system uses **SQLite** with **SQLAlchemy 2.0** and **Alembic**.

### Database Constraints & Concurrency Protection
To satisfy requirement #4:
1. `whatsapp_appointments` table has a **database-level unique constraint**:
   ```sql
   CONSTRAINT uq_doctor_slot UNIQUE (doctor_id, slot)
   ```
2. When two requests attempt to book the exact same doctor and slot simultaneously, the SQLite unique constraint raises an `IntegrityError`.
3. `BookingService` intercepts `IntegrityError`, immediately rolls back the transaction, and returns an HTTP `409 Conflict`.
4. Indexes are applied on `(doctor_id, slot)` and `user_phone` for sub-millisecond lookups.

### Migration Commands
```powershell
# Apply all pending migrations to head
cd backend
..\.venv\Scripts\alembic.exe upgrade head

# Create a new auto-generated migration (if models change)
..\.venv\Scripts\alembic.exe revision --autogenerate -m "Add new column"

# Rollback one migration
..\.venv\Scripts\alembic.exe downgrade -1
```

### Database Reset Procedure
To reset the local database from scratch:
```powershell
cd backend
del appointments.db
..\.venv\Scripts\alembic.exe upgrade head
..\.venv\Scripts\python.exe -c "import sqlite3; conn = sqlite3.connect('appointments.db'); conn.executescript(open('seed_data.sql').read()); conn.commit(); print('Database reset successfully.')"
cd ..
```

---

## 7. API Endpoints & Swagger UI

FastAPI exposes interactive API documentation:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Core Endpoints

#### 1. Create Appointment
`POST /appointments/`

**Request:**
```bash
curl -X POST "http://localhost:8000/appointments/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_phone": "+14155552671",
    "doctor_id": 1,
    "slot": "2026-10-20T10:00:00"
  }'
```

**Success Response (HTTP 201):**
```json
{
  "id": 1,
  "user_phone": "+14155552671",
  "doctor_id": 1,
  "slot": "2026-10-20T10:00:00",
  "status": "CONFIRMED",
  "created_at": "2026-10-14T17:15:00.000000",
  "doctor_name": "Dr. Alice Smith"
}
```

**Conflict Response (HTTP 409):**
```json
{
  "detail": "Doctor Dr. Alice Smith is already booked at 2026-10-20 10:00 AM."
}
```

**Validation Error (HTTP 400):**
```json
{
  "detail": "Appointment slot cannot be in the past."
}
```

---

#### 2. List Appointments
`GET /appointments/?doctor_id=1&appointment_date=2026-10-20`

**Response (HTTP 200):**
```json
[
  {
    "id": 1,
    "user_phone": "+14155552671",
    "doctor_id": 1,
    "slot": "2026-10-20T10:00:00",
    "status": "CONFIRMED",
    "created_at": "2026-10-14T17:15:00.000000",
    "doctor_name": "Dr. Alice Smith"
  }
]
```

---

#### 3. Cancel Appointment
`DELETE /appointments/1`

**Response (HTTP 200):**
```json
{
  "status": "success",
  "message": "Appointment 1 cancelled."
}
```

---

#### 4. Doctors & Available Slots
- `GET /doctors/`: Retrieve all registered active doctors.
- `GET /doctors/{doctor_id}/slots?target_date=2026-10-20`: Returns all unbooked 30-minute slots between 09:00 AM and 05:00 PM for the doctor on that date.

---

#### 5. Health Check
`GET /health`

**Response (HTTP 200):**
```json
{
  "status": "ok",
  "app_name": "WhatsApp Appointment Scheduler",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2026-10-14T17:30:00.000000"
}
```

---

## 8. Natural Language WhatsApp Webhook

`POST /whatsapp/`

Accepts incoming messages from the WhatsApp simulator or live Meta Cloud webhooks.

### Supported Natural Language Patterns
- `"Book appointment with Dr. A at 10 AM tomorrow."`
- `"I need an appointment with Dr. B on 20 October at 3 PM."`
- `"Book Dr. A today at 10:30 AM."`
- `"Book Dr. Charlie Brown next Friday at 2 PM."`

### Webhook Execution Flow
1. **Idempotency check**: Re-delivered messages with the same `message_id` return the cached response without creating duplicate bookings.
2. **Natural Language Parser**: Extracts doctor name/alias, target date, and time.
3. **Clarification on Ambiguity**: If any mandatory information is missing (e.g. user forgot the time or doctor), returns a clarification prompt.
4. **Availability & Booking**: Validates slot rules. If free, books appointment and returns confirmation.
5. **Conflict Handling**: If slot is already booked, returns rejection message and automatically suggests available alternative slots for that doctor on that date.

### Mock Request Example
```bash
curl -X POST "http://localhost:8000/whatsapp/" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "+14155552671",
    "text": "Book appointment with Dr. A at 10 AM tomorrow",
    "message_id": "msg_001"
  }'
```

**Response (HTTP 200):**
```json
{
  "status": "success",
  "reply": "✅ Appointment Confirmed!\nDoctor: Dr. Alice Smith (Cardiology)\nTime: Wednesday, 15 October 2026 at 10:00 AM\nBooking ID: #3\nPatient Phone: +14155552671",
  "appointment": {
    "id": 3,
    "user_phone": "+14155552671",
    "doctor_id": 1,
    "slot": "2026-10-15T10:00:00",
    "status": "CONFIRMED",
    "created_at": "2026-10-14T17:35:00.000000",
    "doctor_name": "Dr. Alice Smith"
  },
  "suggested_slots": null,
  "message_id": "msg_001"
}
```

---

## 9. Meta WhatsApp Cloud API Integration (Live Mode)

The system supports the official **Meta WhatsApp Cloud API (Graph API v19.0)**.

### Live Configuration Steps
1. Create a Meta Developer App at [developers.facebook.com](https://developers.facebook.com).
2. Add **WhatsApp Product** to your app and obtain:
   - `META_PHONE_NUMBER_ID`
   - `META_WHATSAPP_TOKEN` (Permanent System User Token)
   - `META_APP_SECRET`
3. Configure your `.env` file:
   ```env
   WHATSAPP_PROVIDER=meta
   META_WHATSAPP_TOKEN=EAA...
   META_PHONE_NUMBER_ID=123456789012345
   META_VERIFY_TOKEN=my_custom_verify_token
   META_APP_SECRET=a1b2c3d4e5f6...
   ```
4. Expose your local backend publicly using a secure tunnel:
   ```bash
   ngrok http 8000
   ```
5. In Meta Developer Portal -> WhatsApp -> Configuration:
   - **Callback URL**: `https://<your-subdomain>.ngrok-free.app/whatsapp/`
   - **Verify Token**: `my_custom_verify_token`
   - Click **Verify and Save**. The backend handles the `GET /whatsapp/?hub.mode=subscribe` challenge automatically.
   - Subscribe to the `messages` webhook field.

Incoming WhatsApp messages from mobile phones are automatically verified via HMAC-SHA256 (`X-Hub-Signature-256`), parsed, booked, and outbound WhatsApp replies are delivered directly to the user's phone via Meta's Graph API.

---

## 10. React Web Application

Built with **React 18** and **Vite**, styled with modern CSS.

### Key Features
1. **Interactive WhatsApp Simulator**:
   - iPhone-style mockup with verified contact badge.
   - Custom mock phone number input.
   - Quick prompt chips for testing instant bookings, conflict resolution, and ambiguity handling.
   - Outbound & incoming chat bubble aesthetics with timestamps and checkmarks.
   - Clickable alternative slot suggestion buttons.
2. **Booked Appointments Dashboard**:
   - Live appointments table fetching directly from `/appointments/`.
   - Real-time search by patient phone and filter by doctor.
   - Cancellation button with confirmation.
3. **REST Booking Form**:
   - Interactive booking form invoking `POST /appointments/`.
   - Live calendar picker with available 30-minute slot pill buttons.
4. **Doctor Roster & Availability Inspector**:
   - Cards showing doctors, specialties, and open slots for any selected date.
5. **Real-Time Health Status**:
   - Live polling health badge in the navbar indicating backend & SQLite status.

---

## 11. Generated Python Client SDK (`wa_sdk`)

The Python SDK was generated directly from the running FastAPI application using the official **OpenAPI Generator CLI**:

```bash
# Command used to generate the SDK:
openapi-generator-cli generate -i http://localhost:8000/openapi.json -g python -o wa_sdk --additional-properties=packageName=wa_sdk
```

Or execute the provided batch script:
```bat
scripts\generate_sdk.bat
```

### SDK Usage Example

```python
from datetime import datetime, timedelta
import wa_sdk
from wa_sdk.api.health_api import HealthApi
from wa_sdk.api.doctors_api import DoctorsApi
from wa_sdk.api.appointments_api import AppointmentsApi
from wa_sdk.models.appointment_create import AppointmentCreate

# Initialize client
config = wa_sdk.Configuration(host="http://localhost:8000")
client = wa_sdk.ApiClient(configuration=config)

# 1. Health check
health_api = HealthApi(client)
print("Health:", health_api.check_health_health_get().status)

# 2. List doctors
doctors_api = DoctorsApi(client)
doctors = doctors_api.list_doctors_doctors_get()
print(f"Doctors ({len(doctors)}):", [d.name for d in doctors])

# 3. Book an appointment
appointments_api = AppointmentsApi(client)
slot_time = (datetime.utcnow() + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)

new_appt = AppointmentCreate(
    user_phone="+14155554321",
    doctor_id=1,
    slot=slot_time
)

response = appointments_api.create_appointment_appointments_post(appointment_create=new_appt)
print(f"Booked Appointment #{response.id} for {response.slot}")
```

To run the complete executable example:
```powershell
.\.venv\Scripts\python.exe wa_sdk/example.py
```

---

## 12. Automated Testing

Automated tests are implemented using **pytest** and FastAPI's **TestClient** with an isolated in-memory SQLite database (`sqlite:///:memory:`). Tests never mutate the development database.

### Running Backend Tests
```powershell
.\.venv\Scripts\pytest.exe backend/tests -v
```

### Test Coverage Summary (27 Tests)
- `test_health_check`: Verifies `/health` returns 200 OK and database connectivity.
- `test_create_appointment_success`: Validates successful appointment creation and schema response.
- `test_reject_invalid_phone_number`: Validates phone format regex validation.
- `test_reject_unknown_doctor`: Verifies 404 response on unknown doctor ID.
- `test_reject_past_appointment`: Verifies 400 rejection for appointments in the past.
- `test_reject_outside_working_hours`: Rejects slots before 09:00 or after 17:00.
- `test_reject_misaligned_slot_time`: Rejects slots that do not align with 30-minute intervals.
- `test_reject_duplicate_booking_conflict`: Verifies HTTP 409 Conflict when a slot is already booked.
- `test_two_patients_attempting_same_slot_concurrency`: Simulates race condition and verifies DB constraint safety.
- `test_list_and_filter_appointments`: Verifies query filters by doctor and phone.
- `test_parse_tomorrow_10am`: Tests natural language relative date/time parsing.
- `test_parse_explicit_date_and_time`: Tests explicit date formatting ("20 October at 3 PM").
- `test_parse_today_1030am`: Tests "today at 10:30 AM" parsing.
- `test_parse_missing_time`: Validates clarification prompt on missing time.
- `test_parse_missing_doctor`: Validates clarification prompt on missing doctor.
- `test_parse_missing_date`: Validates clarification prompt on missing date.
- `test_parse_empty_or_greeting`: Tests helpful greeting message.
- `test_sdk_imports`: Validates `wa_sdk` package imports.
- `test_sdk_model_instantiation`: Validates SDK Pydantic model serialization.
- `test_meta_webhook_verification`: Tests Meta hub challenge handshake.
- `test_meta_webhook_verification_bad_token`: Verifies 403 on invalid token.
- `test_whatsapp_booking_success`: End-to-end mock webhook booking.
- `test_whatsapp_booking_ambiguous_message`: Webhook response on ambiguous input.
- `test_whatsapp_booking_unknown_doctor`: Prompts with roster when doctor is unknown.
- `test_whatsapp_booking_conflict_with_alternatives`: Verifies slot alternatives returned on conflict.
- `test_whatsapp_idempotency_duplicate_webhook`: Verifies deduplication of re-delivered webhooks.
- `test_meta_cloud_api_format_payload`: Parses real Meta WhatsApp Cloud API JSON structure.

---

## 13. Troubleshooting Guide

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| **`Port 8000 already in use`** | Another process is holding port 8000 | Run `netstat -ano \| findstr :8000` and kill the PID via `taskkill /PID <PID> /F`, or change `PORT` in `.env`. |
| **`npm.ps1 cannot be loaded (Execution Policy)`** | PowerShell script restriction on Windows | Use `npm.cmd` directly or run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`. In batch scripts (`.bat`), `npm` invokes `npm.cmd` automatically. |
| **`Java not found during SDK generation`** | OpenAPI Generator requires Java 11+ | Install Java 17 (e.g. Eclipse Temurin) or verify that `java -version` returns a valid runtime. |
| **`SQLite Database is locked`** | Multiple processes writing simultaneously | The backend uses `connect_args={"check_same_thread": False}` and transactional rollback. Ensure old orphaned processes are closed. |
| **`CORS Error in Browser`** | Frontend running on non-default port | Ensure your frontend URL is listed in `CORS_ORIGINS` inside `.env`. |

---

## 14. Business Rules & Assumptions

1. **Slot Duration**: Default 30 minutes (configurable via `SLOT_DURATION_MINUTES`).
2. **Working Hours**: Default 09:00 AM to 05:00 PM (17:00). The last available slot begins at 04:30 PM.
3. **Timezone**: All slot calculations and comparisons are anchored to UTC (configurable via `APP_TIMEZONE`).
4. **Phone Numbers**: Must be between 7 and 20 digits, optionally beginning with `+`.
5. **Concurrency**: Guaranteed at the database level via SQLite `UniqueConstraint("doctor_id", "slot")`.
6. **Provider Mock Mode**: Enabled by default so developers and reviewers can test all WhatsApp flows without needing Meta Developer credentials or phone numbers.
