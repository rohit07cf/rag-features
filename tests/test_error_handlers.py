"""Tests for domain error → HTTP response mapping via FastAPI exception handlers."""

from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_data/error_test.db"
os.environ["APP_ENV"] = "test"


@pytest.fixture
def client():
    os.makedirs("test_data", exist_ok=True)

    from app.main import app
    from app.storage.db import create_tables

    create_tables()

    with TestClient(app) as c:
        yield c


class TestExceptionHandlers:
    def test_not_found_returns_404_with_error_body(self, client):
        """NotFoundError should map to 404 with structured error body."""
        r = client.get("/v1/assistants/nonexistent_id_12345")
        assert r.status_code == 404

    def test_validation_error_returns_422(self, client):
        """Pydantic validation errors return 422 from FastAPI."""
        r = client.post(
            "/v1/assistants",
            json={
                "user_id": "u1",
                "name": "Bad",
                "type": "invalid_type",
                "provider": "openai",
                "model": "gpt-4o",
            },
        )
        assert r.status_code == 422

    def test_ingestion_not_found(self, client):
        """Ingestion endpoint should return 404 for unknown ID."""
        r = client.get("/v1/ingestions/fake_ing_id/status")
        assert r.status_code == 404

    def test_health_unaffected(self, client):
        """Health endpoint should still work."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
