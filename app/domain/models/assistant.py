"""Pydantic domain models for assistant-related schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.domain.models.enums import AssistantType, ChunkStrategy, LLMProvider


class AssistantCreateCommand(BaseModel):
    """Validated command for creating an assistant."""

    user_id: str
    name: str
    type: AssistantType
    provider: LLMProvider
    model: str
    system_prompt: str = ""
    default_chunk_strategy: ChunkStrategy = ChunkStrategy.RECURSIVE


class AssistantDTO(BaseModel):
    """Data transfer object for assistant responses."""

    id: str
    user_id: str
    name: str
    type: str
    provider: str
    model: str
    system_prompt: str
    default_chunk_strategy: str
    created_at: datetime


class RagStatusDTO(BaseModel):
    """RAG readiness status for an assistant."""

    has_documents: bool
    num_docs: int
    total_ingestions: int
    last_ingestion_state: Optional[str]
