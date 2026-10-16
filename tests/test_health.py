"""Tests for the optional API health endpoint."""

from fastapi.testclient import TestClient

from researchmind.api.main import app


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "phase": "2"}
