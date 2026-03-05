"""Base interface for text chunkers (Strategy Pattern).

Chunking is crucial for RAG because:

1. LLMs have context limits (GPT-4: ~8000 tokens)
2. Whole documents are too long to fit in context
3. We need to retrieve relevant parts, not entire books

Chunking Strategies:
- Recursive: Split by paragraphs, then sentences, then words
- Token-based: Split by token count (500 tokens per chunk)
- Heading-aware: Split at document headings/sections
- Adaptive: Smart splitting based on content structure
- Contextual: Use AI (Doc Intelligence) to understand document structure

Good chunks preserve meaning while fitting in LLM context windows.

All chunking strategies implement ChunkingStrategy. Selection is
done by ChunkStrategy enum via the chunker registry in this module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

# Re-export the Pydantic Chunk model so existing imports still work.
from app.domain.models.chunk import Chunk

__all__ = ["Chunk", "ChunkingStrategy", "get_chunker"]


class ChunkingStrategy(ABC):
    """Strategy interface that all chunkers implement.

    Real-Time Chunking Example:
    Input: "Chapter 1: Introduction\n\nAI is transforming... (2000 words)"

    Output: [
        Chunk(text="Chapter 1: Introduction\n\nAI is transforming...", metadata={...}),
        Chunk(text="The benefits of AI include...", metadata={...}),
        ...
    ]

    Each chunk includes text + metadata (page numbers, headings, etc.)
    """

    @abstractmethod
    def chunk(self, text: str, document_id: str = "", **kwargs) -> list[Chunk]:
        """Split text into meaningful chunks.

        Args:
            text: Full document text
            document_id: For tracking chunk provenance
            **kwargs: Strategy-specific parameters

        Returns:
            List of Chunk objects with text and metadata
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for logging and debugging."""
        ...


# Keep backward-compatible alias
BaseChunker = ChunkingStrategy


def get_chunker(strategy: str) -> ChunkingStrategy:
    """Registry/factory — returns a chunker instance for the given strategy name.

    Strategy Selection Guide:
    - "recursive": Good default, works with any document
    - "heading_aware": Best for structured documents (reports, manuals)
    - "adaptive": Smart splitting based on content analysis
    - "contextual_docintel": Uses Azure AI to understand document layout
    - "token": Simple token-based splitting (fastest)

    Real-time usage: Assistant config specifies strategy, system selects
    appropriate chunker for document type.
    """
    from app.rag.chunking.adaptive import AdaptiveChunker
    from app.rag.chunking.contextual_docintel import ContextualDocIntelChunker
    from app.rag.chunking.heading_aware import HeadingAwareChunker
    from app.rag.chunking.recursive import RecursiveChunker
    from app.rag.chunking.token import TokenChunker

    registry: dict[str, type[ChunkingStrategy]] = {
        "recursive": RecursiveChunker,  # Default: paragraph → sentence → word
        "token": TokenChunker,  # Simple: fixed token windows
        "heading_aware": HeadingAwareChunker,  # Smart: split at headings
        "adaptive": AdaptiveChunker,  # Advanced: content-aware splitting
        "contextual_docintel": ContextualDocIntelChunker,  # AI-powered layout analysis
    }
    cls = registry.get(strategy, RecursiveChunker)  # Default to recursive
    return cls()
