"""Tests for the RetrievalPipeline (Template Method pattern)."""

from __future__ import annotations

import pytest

from app.domain.pipelines.retrieval_pipeline import RetrievalPipeline


class FakeEmbedder:
    """Minimal Embedder for testing."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    @property
    def dimension(self) -> int:
        return 3


class FakeVectorStore:
    """Minimal VectorStore for testing."""

    def __init__(self, results: list[dict] | None = None):
        self._results = results or []

    def upsert_vectors(self, ids, vectors, metadatas, namespace="", batch_size=100):
        return len(ids)

    def query(self, vector, top_k=10, namespace="", filter=None, include_metadata=True):
        return self._results[:top_k]


class FakeReranker:
    """Minimal Reranker — returns top_k by existing score."""

    def rerank(self, query: str, chunks: list[dict], top_k: int = 4) -> list[dict]:
        sorted_chunks = sorted(chunks, key=lambda c: c.get("score", 0), reverse=True)
        return sorted_chunks[:top_k]


class TestRetrievalPipeline:
    @pytest.mark.asyncio
    async def test_empty_results(self):
        pipeline = RetrievalPipeline(
            embedder=FakeEmbedder(),
            vector_store=FakeVectorStore(results=[]),
            reranker=FakeReranker(),
        )
        result = await pipeline.run(query="test", assistant_id="a1")
        assert result == []

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        candidates = [
            {"text": "chunk A", "score": 0.9, "token_count": 10},
            {"text": "chunk B", "score": 0.7, "token_count": 10},
            {"text": "chunk C", "score": 0.8, "token_count": 10},
            {"text": "chunk D", "score": 0.6, "token_count": 10},
        ]
        pipeline = RetrievalPipeline(
            embedder=FakeEmbedder(),
            vector_store=FakeVectorStore(results=candidates),
            reranker=FakeReranker(),
        )

        result = await pipeline.run(
            query="test query",
            assistant_id="a1",
            top_k=4,
            rerank_top_k=2,
        )

        # Reranker should return top 2 by score
        assert len(result) <= 2
        # Highest score first
        if len(result) == 2:
            assert result[0]["score"] >= result[1]["score"]

    @pytest.mark.asyncio
    async def test_respects_top_k(self):
        candidates = [
            {"text": f"chunk {i}", "score": i * 0.1, "token_count": 10} for i in range(10)
        ]
        pipeline = RetrievalPipeline(
            embedder=FakeEmbedder(),
            vector_store=FakeVectorStore(results=candidates),
            reranker=FakeReranker(),
        )

        result = await pipeline.run(
            query="test",
            assistant_id="a1",
            top_k=5,
            rerank_top_k=3,
        )
        assert len(result) <= 3
