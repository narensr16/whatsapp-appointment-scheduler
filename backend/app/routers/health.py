"""Health check router for monitoring and liveness probes."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.dependencies import get_db
from app.schemas import HealthResponse
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Returns application health status, version, and verifies database connectivity."
)
def check_health(db: Session = Depends(get_db)):
    """Verifies that the API and SQLite database are fully operational."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database connectivity check failed: {str(exc)}"
        )

    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        database=db_status,
        timestamp=datetime.utcnow()
    )
