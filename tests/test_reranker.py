"""Tests for reranking logic."""

from __future__ import annotations

from src.rag.retrieval.rerank.external_placeholder import ExternalReranker
from src.rag.retrieval.rerank.local_reranker import LocalReranker


class TestLocalReranker:
    def test_rerank_empty(self):
        reranker = LocalReranker()
        result = reranker.rerank("query", [], top_k=3)
        assert result == []

    def test_rerank_fallback(self):
        """When model is unavailable, should fall back to vector score sorting."""
        reranker = LocalReranker()
        reranker._model = "unavailable"  # Force fallback

        chunks = [
            {"text": "low relevance", "score": 0.5},
            {"text": "high relevance", "score": 0.9},
            {"text": "medium relevance", "score": 0.7},
        ]

        result = reranker.rerank("test query", chunks, top_k=2)
        assert len(result) == 2
        assert result[0]["score"] == 0.9  # Highest score first
        assert result[1]["score"] == 0.7

    def test_rerank_respects_top_k(self):
        reranker = LocalReranker()
        reranker._model = "unavailable"

        chunks = [
            {"text": f"chunk {i}", "score": i * 0.1}
            for i in range(10)
        ]

        result = reranker.rerank("query", chunks, top_k=3)
        assert len(result) == 3


class TestExternalReranker:
    def test_placeholder_sorts_by_score(self):
        reranker = ExternalReranker()
        chunks = [
            {"text": "a", "score": 0.3},
            {"text": "b", "score": 0.8},
            {"text": "c", "score": 0.5},
        ]
        result = reranker.rerank("query", chunks, top_k=2)
        assert len(result) == 2
        assert result[0]["score"] == 0.8
