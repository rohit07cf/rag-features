"""Pydantic domain models for ingestion-related concepts."""

from __future__ import annotations

from pydantic import BaseModel

from src.app.domain.models.enums import ChunkStrategy, IngestionState


class IngestionCommand(BaseModel):
    """Validated command for starting an ingestion."""

    assistant_id: str
    user_id: str
    document_id: str
    filename: str
    file_path: str
    chunk_strategy: ChunkStrategy = ChunkStrategy.RECURSIVE


class IngestionProgressDTO(BaseModel):
    """Ingestion progress snapshot."""

    ingestion_id: str
    state: IngestionState
    current_step: str
    progress_pct: int
    error_message: str = ""
