"""Activity: chunk text using the selected strategy."""

from __future__ import annotations

from temporalio import activity


@activity.defn
async def chunk_text(params: dict) -> list[dict]:
    """Chunk text using the specified strategy.

    Args:
        params: {"text": str, "document_id": str, "strategy": str, "file_path": str}

    Returns:
        List of chunk dicts
    """
    text = params["text"]
    document_id = params["document_id"]
    strategy = params["strategy"]
    file_path = params.get("file_path", "")

    activity.logger.info(
        "Chunking document %s with strategy=%s (%d chars)",
        document_id, strategy, len(text),
    )

    chunker = _get_chunker(strategy)
    chunks = chunker.chunk(text, document_id=document_id, file_path=file_path)

    activity.logger.info("Produced %d chunks", len(chunks))

    return [c.to_dict() for c in chunks]


def _get_chunker(strategy: str):
    """Factory for chunker instances."""
    if strategy == "recursive":
        from src.rag.chunking.recursive import RecursiveChunker
        return RecursiveChunker()
    elif strategy == "token":
        from src.rag.chunking.token import TokenChunker
        return TokenChunker()
    elif strategy == "heading_aware":
        from src.rag.chunking.heading_aware import HeadingAwareChunker
        return HeadingAwareChunker()
    elif strategy == "adaptive":
        from src.rag.chunking.adaptive import AdaptiveChunker
        return AdaptiveChunker()
    elif strategy == "contextual_docintel":
        from src.rag.chunking.contextual_docintel import ContextualDocIntelChunker
        return ContextualDocIntelChunker()
    else:
        from src.rag.chunking.recursive import RecursiveChunker
        return RecursiveChunker()
