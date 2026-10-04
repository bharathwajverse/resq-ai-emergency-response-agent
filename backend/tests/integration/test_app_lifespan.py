"""
Integration Tests for ResQ-AI FastAPI Application Lifespan, Endpoints & Seeding.
Verifies server startup, CORS headers, disclaimer middleware, health checks, and database seeding.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func

from app.main import app
from app.config import get_settings
from app.models import Hospital, Ambulance, Resource, Road
from app.services.seed_service import seed_initial_data, reset_database

settings = get_settings()


def test_root_endpoint_metadata(client: TestClient):
    """Verify GET / returns application metadata, demo mode status, and disclaimer."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "online"
    assert data["app"] == settings.PROJECT_NAME
    assert data["version"] == settings.PROJECT_VERSION
    assert "demo_mode" in data
    assert data["disclaimer"] == settings.DISCLAIMER_TEXT

    # Check custom headers
    assert "X-ResQ-AI-Disclaimer" in response.headers
    assert response.headers["X-ResQ-AI-Disclaimer"] == settings.DISCLAIMER_TEXT
    assert "X-Response-Time-Ms" in response.headers


def test_health_check_endpoint(client: TestClient):
    """Verify GET /health probes database connectivity and returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["disclaimer"] == settings.DISCLAIMER_TEXT


def test_cors_preflight_headers(client: TestClient):
    """Verify OPTIONS request receives CORS allow headers."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_idempotent_database_seeder(db_session):
    """Verify seeder creates ambulances A1-A3, hospitals H1-H2, resources, and roads idempotently."""
    # First seed run
    counts1 = seed_initial_data(db_session, force=True)
    assert counts1["hospitals"] == 2
    assert counts1["ambulances"] == 3
    assert counts1["resources"] == 5
    assert counts1["roads"] == 21

    # Verify hospital counts
    hospitals = db_session.scalars(select(Hospital)).all()
    assert len(hospitals) == 2
    h_codes = {h.code for h in hospitals}
    assert h_codes == {"H1", "H2"}

    # Verify ambulance counts & capacities
    ambulances = db_session.scalars(select(Ambulance)).all()
    assert len(ambulances) == 3
    a1 = next(a for a in ambulances if a.code == "A1")
    a2 = next(a for a in ambulances if a.code == "A2")
    a3 = next(a for a in ambulances if a.code == "A3")

    assert a1.capacity == 4 and a1.status == "Available"
    assert a2.capacity == 6 and a2.status == "Available"
    assert a3.capacity == 6 and a3.status == "Maintenance"

    # Second seed run without force: must not create duplicates
    counts2 = seed_initial_data(db_session, force=False)
    assert db_session.scalar(select(func.count()).select_from(Hospital)) == 2
    assert db_session.scalar(select(func.count()).select_from(Ambulance)) == 3
    assert db_session.scalar(select(func.count()).select_from(Resource)) == 5
    assert db_session.scalar(select(func.count()).select_from(Road)) == 21


def test_database_reset_service(db_session):
    """Verify reset_database purges seed entities and repopulates canonical state."""
    # Seed initial
    seed_initial_data(db_session, force=True)
    assert db_session.scalar(select(func.count()).select_from(Hospital)) == 2

    # Reset
    reset_counts = reset_database(db_session)
    assert reset_counts["hospitals"] == 2
    assert reset_counts["ambulances"] == 3
    assert db_session.scalar(select(func.count()).select_from(Hospital)) == 2
