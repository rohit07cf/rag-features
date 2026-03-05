"""Activity: embed chunk texts in batches."""

from __future__ import annotations

import json
import os

from temporalio import activity

from app.rag.utils.batching import batch_items
from app.rag.utils.ids import make_chunk_id


@activity.defn
async def embed_batches(params: dict) -> dict:
    """Embed chunks in batches and upsert to Pinecone.

    Args:
        params: {"chunks_file": str, "document_id": str, "assistant_id": str}

    Returns:
        {"count": int} — number of vectors upserted
    """
    chunks_file = params["chunks_file"]
    document_id = params["document_id"]
    assistant_id = params["assistant_id"]

    # Load chunks from file
    with open(chunks_file, 'r') as f:
        chunks = json.load(f)

    activity.logger.info("Embedding and upserting %d chunks for document %s", len(chunks), document_id)

    from app.rag.embeddings.openai_embedder import OpenAIEmbedder
    from app.rag.vectorstore.pinecone_store import PineconeStore

    embedder = OpenAIEmbedder()
    store = PineconeStore()

    # Process in batches of 50
    batches = batch_items(chunks, batch_size=50)
    total_upserted = 0

    for batch in batches:
        texts = [c.get("text", "") for c in batch]
        vectors = await embedder.embed_texts(texts)

        # Prepare data for upsert
        ids = [make_chunk_id(document_id, c.get("chunk_index", 0)) for c in batch]
        metadatas = [
            {
                "text": c.get("text", "")[:1000],  # Pinecone metadata size limit
                "document_id": document_id,
                "assistant_id": assistant_id,
                "chunk_index": c.get("chunk_index", 0),
                "page_numbers": c.get("page_numbers", []),
                "heading_path": c.get("heading_path", []),
                "section_title": c.get("section_title", ""),
            }
            for c in batch
        ]

        # Upsert this batch
        batch_count = store.upsert_vectors(
            ids=ids,
            vectors=vectors,
            metadatas=metadatas,
        )
        total_upserted += batch_count

    # Clean up the temporary chunks file
    os.unlink(chunks_file)

    activity.logger.info("Embedded and upserted %d chunks total", total_upserted)
    return {"count": total_upserted}
