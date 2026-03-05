"""Placeholder for external reranking API (Cohere, Jina, etc.)."""

from __future__ import annotations

from app.rag.retrieval.rerank.base import BaseReranker


class ExternalReranker(BaseReranker):
    """Placeholder for calling an external reranking service.

    In production, this would call Cohere Rerank, Jina Reranker,
    or a hosted cross-encoder API.
    """

    def __init__(self, api_key: str = "", model: str = "rerank-english-v3.0"):
        self._api_key = api_key
        self._model = model

    def rerank(self, query: str, chunks: list[dict], top_k: int = 4) -> list[dict]:
        # Placeholder: return chunks sorted by existing score
        sorted_chunks = sorted(chunks, key=lambda c: c.get("score", 0), reverse=True)
        return sorted_chunks[:top_k]
