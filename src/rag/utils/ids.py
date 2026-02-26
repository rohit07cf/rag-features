"""ID generation utilities."""

from __future__ import annotations

import hashlib
import uuid


def make_chunk_id(document_id: str, chunk_index: int) -> str:
    """Deterministic chunk ID from document + index."""
    raw = f"{document_id}::{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def make_document_id() -> str:
    return uuid.uuid4().hex[:12]


def make_workflow_id(prefix: str = "ingest") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"
