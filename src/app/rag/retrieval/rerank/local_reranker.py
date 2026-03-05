"""Local cross-encoder reranker using sentence-transformers."""

from __future__ import annotations

from src.app.rag.retrieval.rerank.base import BaseReranker


class LocalReranker(BaseReranker):
    """Cross-encoder reranker using a small model for relevance scoring.

    Falls back to vector similarity scores if the model is unavailable.
    """

    MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self):
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder

                self._model = CrossEncoder(self.MODEL_NAME)
            except Exception:
                self._model = "unavailable"

    def rerank(self, query: str, chunks: list[dict], top_k: int = 4) -> list[dict]:
        if not chunks:
            return []

        self._load_model()

        if self._model == "unavailable":
            # Fallback: sort by existing vector similarity score
            sorted_chunks = sorted(chunks, key=lambda c: c.get("score", 0), reverse=True)
            return sorted_chunks[:top_k]

        # Cross-encoder scoring
        pairs = [(query, chunk.get("text", "")) for chunk in chunks]
        scores = self._model.predict(pairs)

        for i, chunk in enumerate(chunks):
            chunk["rerank_score"] = float(scores[i])

        sorted_chunks = sorted(chunks, key=lambda c: c.get("rerank_score", 0), reverse=True)
        return sorted_chunks[:top_k]
