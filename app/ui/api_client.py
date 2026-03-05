"""HTTP client for the FastAPI backend."""

from __future__ import annotations

import os

import httpx

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _url(path: str) -> str:
    return f"{BASE_URL}{path}"


# ── Assistants ────────────────────────────────────────────────────


def create_assistant(data: dict) -> dict:
    r = httpx.post(_url("/v1/assistants"), json=data, timeout=10)
    r.raise_for_status()
    return r.json()


def get_assistant(assistant_id: str) -> dict:
    r = httpx.get(_url(f"/v1/assistants/{assistant_id}"), timeout=10)
    r.raise_for_status()
    return r.json()


def list_assistants(user_id: str) -> list[dict]:
    r = httpx.get(_url("/v1/assistants"), params={"user_id": user_id}, timeout=10)
    r.raise_for_status()
    return r.json()


def get_rag_status(assistant_id: str) -> dict:
    r = httpx.get(_url(f"/v1/assistants/{assistant_id}/rag_status"), timeout=10)
    r.raise_for_status()
    return r.json()


# ── Documents / Ingestion ────────────────────────────────────────


def upload_documents(
    assistant_id: str,
    user_id: str,
    chunk_strategy: str,
    files: list[tuple[str, bytes, str]],
) -> list[dict]:
    """Upload files to the backend.

    Args:
        files: List of (filename, bytes_content, mime_type)
    """
    multipart_files = [("files", (name, data, mime)) for name, data, mime in files]
    r = httpx.post(
        _url("/v1/documents/upload"),
        data={
            "assistant_id": assistant_id,
            "user_id": user_id,
            "chunk_strategy": chunk_strategy,
        },
        files=multipart_files,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def get_ingestion_status(ingestion_id: str) -> dict:
    r = httpx.get(_url(f"/v1/ingestions/{ingestion_id}/status"), timeout=10)
    r.raise_for_status()
    return r.json()


# ── Chat ─────────────────────────────────────────────────────────


def chat(assistant_id: str, user_id: str, message: str, conversation_id: str | None = None) -> dict:
    payload = {
        "assistant_id": assistant_id,
        "user_id": user_id,
        "message": message,
    }
    if conversation_id:
        payload["conversation_id"] = conversation_id
    r = httpx.post(_url("/v1/chat"), json=payload, timeout=60)
    r.raise_for_status()
    return r.json()
