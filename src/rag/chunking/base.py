"""Base interface for text chunkers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """A single chunk with text and metadata."""

    text: str
    chunk_index: int = 0
    document_id: str = ""
    page_numbers: list[int] = field(default_factory=list)
    heading_path: list[str] = field(default_factory=list)
    section_title: str = ""
    token_count: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "chunk_index": self.chunk_index,
            "document_id": self.document_id,
            "page_numbers": self.page_numbers,
            "heading_path": self.heading_path,
            "section_title": self.section_title,
            "token_count": self.token_count,
            **self.metadata,
        }


class BaseChunker(ABC):
    """Interface that all chunkers implement."""

    @abstractmethod
    def chunk(self, text: str, document_id: str = "", **kwargs) -> list[Chunk]:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...
