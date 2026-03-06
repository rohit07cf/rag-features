"""Pydantic request / response schemas for the API layer.

These are thin API-boundary models. Enums enforce valid values
via Pydantic validation, eliminating manual if-chains in routes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.models.enums import AssistantType, ChunkStrategy, LLMProvider


# ── Assistants ────────────────────────────────────────────────────


class AssistantCreate(BaseModel):
    user_id: str
    name: str
    type: AssistantType
    provider: LLMProvider
    model: str
    system_prompt: str = ""
    default_chunk_strategy: ChunkStrategy = ChunkStrategy.RECURSIVE


class AssistantResponse(BaseModel):
    id: str
    user_id: str
    name: str
    type: str
    provider: str
    model: str
    system_prompt: str
    default_chunk_strategy: str
    created_at: datetime


class RagStatusResponse(BaseModel):
    has_documents: bool
    num_docs: int
    total_ingestions: int
    last_ingestion_state: Optional[str]


# ── Documents / Ingestion ────────────────────────────────────────


class UploadResponse(BaseModel):
    document_id: str
    ingestion_id: str
    filename: str
    status: str


class IngestionStatusResponse(BaseModel):
    ingestion_id: str
    state: str
    current_step: str
    progress_pct: int
    error_message: str
    workflow_id: str = ""


# ── Chat ─────────────────────────────────────────────────────────


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatRequest(BaseModel):
    assistant_id: str
    user_id: str = "demo_user"
    message: str
    conversation_id: Optional[str] = None


class SourceReference(BaseModel):
    document_id: str
    chunk_id: str
    text_snippet: str
    score: float
    page_numbers: list[int] = Field(default_factory=list)
    heading_path: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    sources: list[SourceReference] = Field(default_factory=list)
    model_used: str = ""
    provider: str = ""


# ── Error ────────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Consistent error response envelope."""

    error_code: str
    message: str
    details: str = ""
