"""Pydantic domain model for document chunks — replaces the dataclass."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """A single chunk with text and structural metadata."""

    text: str
    chunk_index: int = 0
    document_id: str = ""
    page_numbers: list[int] = Field(default_factory=list)
    heading_path: list[str] = Field(default_factory=list)
    section_title: str = ""
    token_count: int = 0
    metadata: dict = Field(default_factory=dict)

    def to_dict(self) -> dict:
        base = {
            "text": self.text,
            "chunk_index": self.chunk_index,
            "document_id": self.document_id,
            "page_numbers": self.page_numbers,
            "heading_path": self.heading_path,
            "section_title": self.section_title,
            "token_count": self.token_count,
        }
        base.update(self.metadata)
        return base
