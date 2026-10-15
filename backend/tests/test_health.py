"""Tests for health check endpoint."""
from fastapi import status


def test_health_check(client):
    """Verify health endpoint returns 200 OK and connected database."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "timestamp" in data
    assert "version" in data
