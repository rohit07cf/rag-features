"""Base reranker interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, chunks: list[dict], top_k: int = 4) -> list[dict]:
        """Rerank chunks by relevance to query.

        Args:
            query: User query
            chunks: Retrieved chunks with 'text' and 'score' keys
            top_k: Number to return

        Returns:
            Reranked list of chunks
        """
        ...
