"""Adaptive chunker — selects strategy based on document characteristics."""

from __future__ import annotations

from src.rag.chunking.base import BaseChunker, Chunk
from src.rag.chunking.heading_aware import HeadingAwareChunker
from src.rag.chunking.recursive import RecursiveChunker
from src.rag.chunking.token import TokenChunker


class AdaptiveChunker(BaseChunker):
    """Automatically picks the best chunking strategy for the document."""

    def __init__(self):
        self._heading = HeadingAwareChunker()
        self._recursive = RecursiveChunker()
        self._token = TokenChunker()

    @property
    def name(self) -> str:
        return "adaptive"

    def chunk(self, text: str, document_id: str = "", **kwargs) -> list[Chunk]:
        # Heuristic: if text has markdown headings, use heading-aware
        heading_count = text.count("\n#")
        if heading_count >= 3:
            return self._heading.chunk(text, document_id, **kwargs)

        # If text is very long with few paragraphs, use token-based
        para_count = text.count("\n\n")
        if para_count < 5 and len(text) > 5000:
            return self._token.chunk(text, document_id, **kwargs)

        # Default: recursive
        return self._recursive.chunk(text, document_id, **kwargs)
