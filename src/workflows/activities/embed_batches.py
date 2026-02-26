"""Activity: embed chunk texts in batches."""

from __future__ import annotations

import asyncio

from temporalio import activity

from src.rag.utils.batching import batch_items
from src.rag.utils.ids import make_chunk_id


@activity.defn
async def embed_batches(params: dict) -> list[dict]:
    """Embed chunks in batches using OpenAI embeddings.

    Args:
        params: {"chunks": list[dict], "document_id": str}

    Returns:
        List of dicts with chunk data + embedding vectors
    """
    chunks = params["chunks"]
    document_id = params["document_id"]

    activity.logger.info("Embedding %d chunks for document %s", len(chunks), document_id)

    from src.rag.embeddings.openai_embedder import OpenAIEmbedder

    embedder = OpenAIEmbedder()

    # Process in batches of 50
    batches = batch_items(chunks, batch_size=50)
    results: list[dict] = []

    for batch in batches:
        texts = [c.get("text", "") for c in batch]
        vectors = await embedder.embed_texts(texts)

        for chunk, vector in zip(batch, vectors):
            chunk_id = make_chunk_id(document_id, chunk.get("chunk_index", 0))
            results.append({
                **chunk,
                "chunk_id": chunk_id,
                "vector": vector,
            })

    activity.logger.info("Embedded %d chunks total", len(results))
    return results
