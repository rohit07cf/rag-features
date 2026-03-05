"""Activity: chunk text using the selected strategy.

Uses the centralized get_chunker() registry from base.py (Strategy Pattern).
"""

from __future__ import annotations

from temporalio import activity

from app.rag.chunking.base import get_chunker


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
        document_id,
        strategy,
        len(text),
    )

    chunker = get_chunker(strategy)
    chunks = chunker.chunk(text, document_id=document_id, file_path=file_path)

    activity.logger.info("Produced %d chunks", len(chunks))

    return [c.to_dict() for c in chunks]
