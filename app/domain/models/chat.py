"""Pydantic domain models for chat-related concepts."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatCommand(BaseModel):
    """Validated command for a chat request."""

    assistant_id: str
    user_id: str = "demo_user"
    message: str
    conversation_id: Optional[str] = None


class SourceReference(BaseModel):
    """A single source citation from RAG retrieval."""

    document_id: str
    chunk_id: str
    text_snippet: str
    score: float
    page_numbers: list[int] = Field(default_factory=list)
    heading_path: list[str] = Field(default_factory=list)


class ChatResult(BaseModel):
    """Result of a chat interaction."""

    answer: str
    conversation_id: str
    sources: list[SourceReference] = Field(default_factory=list)
    model_used: str = ""
    provider: str = ""
