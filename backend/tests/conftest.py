"""Pytest configuration, fixtures, and database isolation."""
import os
import sys
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base
from app.dependencies import get_db
from app.main import app
from app.models import Doctor

# In-memory SQLite database isolated per test session
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh tables in memory before each test and drop them afterward."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Seed sample doctors for tests
    d1 = Doctor(id=1, name="Dr. Alice Smith", specialty="Cardiology", phone="+14155550101")
    d2 = Doctor(id=2, name="Dr. Bob Jones", specialty="Pediatrics", phone="+14155550102")
    session.add_all([d1, d2])
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
