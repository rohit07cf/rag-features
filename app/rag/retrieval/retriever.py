"""High-level retrieval: embed query -> Pinecone -> rerank -> budget."""

from __future__ import annotations

from app.rag.embeddings.openai_embedder import OpenAIEmbedder
from app.rag.retrieval.rerank.local_reranker import LocalReranker
from app.rag.utils.token_budget import fit_chunks_to_budget
from app.rag.vectorstore.pinecone_store import PineconeStore


async def retrieve_and_rerank(
    query: str,
    assistant_id: str,
    top_k: int = 8,
    rerank_top_k: int = 4,
    max_context_tokens: int = 3000,
) -> list[dict]:
    """Full retrieval pipeline: embed -> query -> rerank -> budget trim.

    Args:
        query: User query text
        assistant_id: Used as Pinecone namespace for isolation
        top_k: Initial retrieval count
        rerank_top_k: Reranked result count
        max_context_tokens: Max tokens for context window

    Returns:
        List of chunk dicts with text, metadata, and scores
    """
    embedder = OpenAIEmbedder()
    store = PineconeStore()
    reranker = LocalReranker()

    # 1. Embed query
    query_vector = await embedder.embed_query(query)

    # 2. Retrieve from Pinecone
    candidates = store.query(
        vector=query_vector,
        top_k=top_k,
        namespace=assistant_id,
        filter={"assistant_id": assistant_id},
    )

    if not candidates:
        return []

    # 3. Rerank
    reranked = reranker.rerank(query, candidates, top_k=rerank_top_k)

    # 4. Fit to token budget
    return fit_chunks_to_budget(reranked, max_tokens=max_context_tokens)
