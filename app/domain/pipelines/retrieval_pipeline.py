"""Retrieval pipeline — Template Method pattern.

Staged pipeline: embed query → vector search → rerank → pack context.
Each stage is pluggable via protocol interfaces.
"""

from __future__ import annotations

from app.domain.protocols import Embedder, Reranker, VectorStore
from app.rag.utils.token_budget import fit_chunks_to_budget


class RetrievalPipeline:
    """Orchestrates the multi-stage retrieval process.

    Stages:
    1. Embed the user query
    2. Retrieve candidate chunks from vector store
    3. Rerank candidates for precision
    4. Pack into token budget

    Each component is injected, not hard-coded.
    """

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        reranker: Reranker,
    ):
        self._embedder = embedder
        self._vector_store = vector_store
        self._reranker = reranker

    async def run(
        self,
        query: str,
        assistant_id: str,
        top_k: int = 8,
        rerank_top_k: int = 4,
        max_context_tokens: int = 3000,
    ) -> list[dict]:
        """Execute the full retrieval pipeline.

        Returns:
            List of chunk dicts with text, metadata, and scores.
        """
        # Stage 1: Embed query
        query_vector = await self._embedder.embed_query(query)

        # Stage 2: Retrieve from vector store
        candidates = self._vector_store.query(
            vector=query_vector,
            top_k=top_k,
            namespace=assistant_id,
            filter={"assistant_id": assistant_id},
        )
        if not candidates:
            return []

        # Stage 3: Rerank
        reranked = self._reranker.rerank(query, candidates, top_k=rerank_top_k)

        # Stage 4: Pack into token budget
        return fit_chunks_to_budget(reranked, max_tokens=max_context_tokens)
