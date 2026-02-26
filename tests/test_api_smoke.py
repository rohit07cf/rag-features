"""Smoke tests for FastAPI endpoints."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Set test env before imports
os.environ["DATABASE_URL"] = "sqlite:///./test_data/smoke_test.db"
os.environ["APP_ENV"] = "test"


@pytest.fixture
def client():
    os.makedirs("test_data", exist_ok=True)

    from src.app.main import app
    from src.app.storage.db import create_tables

    create_tables()

    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestAssistantsEndpoints:
    def test_create_and_get_assistant(self, client):
        # Create
        r = client.post("/v1/assistants", json={
            "user_id": "test_user",
            "name": "Test Bot",
            "type": "model_only",
            "provider": "openai",
            "model": "gpt-4.1-mini",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Test Bot"
        assert data["provider"] == "openai"
        assistant_id = data["id"]

        # Get
        r = client.get(f"/v1/assistants/{assistant_id}")
        assert r.status_code == 200
        assert r.json()["name"] == "Test Bot"

    def test_list_assistants(self, client):
        # Create two
        for name in ["Bot A", "Bot B"]:
            client.post("/v1/assistants", json={
                "user_id": "list_user",
                "name": name,
                "type": "rag",
                "provider": "anthropic",
                "model": "claude-3-5-sonnet",
            })

        r = client.get("/v1/assistants", params={"user_id": "list_user"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 2

    def test_invalid_type(self, client):
        r = client.post("/v1/assistants", json={
            "user_id": "test_user",
            "name": "Bad",
            "type": "invalid",
            "provider": "openai",
            "model": "gpt-4o",
        })
        assert r.status_code == 400

    def test_invalid_provider(self, client):
        r = client.post("/v1/assistants", json={
            "user_id": "test_user",
            "name": "Bad",
            "type": "rag",
            "provider": "gemini",
            "model": "gemini-pro",
        })
        assert r.status_code == 400

    def test_404_not_found(self, client):
        r = client.get("/v1/assistants/nonexistent")
        assert r.status_code == 404
