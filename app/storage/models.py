"""SQLModel database models for assistants and ingestion tracking."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


class Assistant(SQLModel, table=True):
    """An assistant configuration (model-only or RAG)."""

    __tablename__ = "assistants"

    id: str = Field(default_factory=_new_id, primary_key=True)
    user_id: str = Field(index=True)
    name: str
    type: str = Field(description="model_only | rag")
    provider: str = Field(description="openai | anthropic")
    model: str
    system_prompt: str = ""
    default_chunk_strategy: str = "recursive"
    created_at: datetime = Field(default_factory=_utcnow)


class IngestionRecord(SQLModel, table=True):
    """Tracks ingestion workflow runs per document."""

    __tablename__ = "ingestion_records"

    id: str = Field(default_factory=_new_id, primary_key=True)
    assistant_id: str = Field(index=True)
    user_id: str = Field(index=True)
    document_id: str
    filename: str = ""
    workflow_id: str = ""
    state: str = Field(default="pending", description="pending|running|succeeded|failed")
    current_step: str = ""
    progress_pct: int = 0
    error_message: str = ""
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: Optional[datetime] = Field(default=None)
