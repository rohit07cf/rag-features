"""Activity: upsert embedded chunks to Pinecone."""

from __future__ import annotations

from temporalio import activity


@activity.defn
async def upsert_pinecone(params: dict) -> dict:
    """Upsert embedded chunks to Pinecone vector store.

    Args:
        params: {"embedded_chunks": list[dict], "assistant_id": str, "document_id": str}

    Returns:
        {"count": int} — number of vectors upserted
    """
    embedded_chunks = params["embedded_chunks"]
    assistant_id = params["assistant_id"]
    document_id = params["document_id"]

    activity.logger.info(
        "Upserting %d vectors for assistant=%s document=%s",
        len(embedded_chunks),
        assistant_id,
        document_id,
    )

    from app.rag.vectorstore.pinecone_store import PineconeStore

    store = PineconeStore()

    ids = [c["chunk_id"] for c in embedded_chunks]
    vectors = [c["vector"] for c in embedded_chunks]
    metadatas = [
        {
            "text": c.get("text", "")[:1000],  # Pinecone metadata size limit
            "document_id": c.get("document_id", document_id),
            "assistant_id": assistant_id,
            "chunk_index": c.get("chunk_index", 0),
            "page_numbers": c.get("page_numbers", []),
            "heading_path": c.get("heading_path", []),
            "section_title": c.get("section_title", ""),
        }
        for c in embedded_chunks
    ]

    count = store.upsert_vectors(
        ids=ids,
        vectors=vectors,
        metadatas=metadatas,
        namespace=assistant_id,
    )

    activity.logger.info("Upserted %d vectors", count)
    return {"count": count}
