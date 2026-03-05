"""Base interface for text chunkers (Strategy Pattern).

All chunking strategies implement ChunkingStrategy. Selection is
done by ChunkStrategy enum via the chunker registry in this module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

# Re-export the Pydantic Chunk model so existing imports still work.
from src.app.domain.models.chunk import Chunk

__all__ = ["Chunk", "ChunkingStrategy", "get_chunker"]


class ChunkingStrategy(ABC):
    """Strategy interface that all chunkers implement."""

    @abstractmethod
    def chunk(self, text: str, document_id: str = "", **kwargs) -> list[Chunk]: ...

    @property
    @abstractmethod
    def name(self) -> str: ...


# Keep backward-compatible alias
BaseChunker = ChunkingStrategy


def get_chunker(strategy: str) -> ChunkingStrategy:
    """Registry/factory — returns a chunker instance for the given strategy name."""
    from src.app.rag.chunking.adaptive import AdaptiveChunker
    from src.app.rag.chunking.contextual_docintel import ContextualDocIntelChunker
    from src.app.rag.chunking.heading_aware import HeadingAwareChunker
    from src.app.rag.chunking.recursive import RecursiveChunker
    from src.app.rag.chunking.token import TokenChunker

    registry: dict[str, type[ChunkingStrategy]] = {
        "recursive": RecursiveChunker,
        "token": TokenChunker,
        "heading_aware": HeadingAwareChunker,
        "adaptive": AdaptiveChunker,
        "contextual_docintel": ContextualDocIntelChunker,
    }
    cls = registry.get(strategy, RecursiveChunker)
    return cls()
