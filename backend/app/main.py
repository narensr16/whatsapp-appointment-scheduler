"""
Main FastAPI Application entry point for WhatsApp-Based Appointment Scheduling System.
Configures CORS, registers routers, handles exceptions, and sets up OpenAPI docs.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import Doctor
from app.routers import health, appointments, whatsapp, doctors

# Configure structured logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("whatsapp_scheduler")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager: verifies schema and populates initial roster if empty."""
    db: Session = SessionLocal()
    try:
        # Check if migrations have been applied
        doctor_count = db.query(Doctor).count()
        if doctor_count == 0:
            logger.info("Database schema detected. Seeding initial sample doctors into database...")
            sample_doctors = [
                Doctor(name="Dr. Alice Smith", specialty="Cardiology", phone="+14155550101"),
                Doctor(name="Dr. Bob Jones", specialty="Pediatrics", phone="+14155550102"),
                Doctor(name="Dr. Charlie Brown", specialty="Dermatology", phone="+14155550103")
            ]
            db.add_all(sample_doctors)
            db.commit()
            logger.info("Initial doctors seeded successfully.")
    except Exception as exc:
        logger.warning(
            "Database table check failed (%s). Ensure Alembic migrations are applied: 'alembic upgrade head'",
            str(exc)
        )
    finally:
        db.close()

    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-quality backend for WhatsApp-Based Appointment Scheduling System. "
        "Supports REST appointment bookings, natural-language WhatsApp webhook interactions, "
        "conflict resolution, and doctor availability management."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global safe error handling
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled server exception at %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )


# Include API Routers
app.include_router(health.router)
app.include_router(appointments.router)
app.include_router(whatsapp.router)
app.include_router(doctors.router)


@app.get("/", tags=["Root"])
def root_redirect():
    """Root endpoint welcoming developers and pointing to Swagger documentation."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "health_url": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
