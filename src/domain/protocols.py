"""Protocol interfaces for dependency inversion.

These define the contracts between domain logic and infrastructure.
Infrastructure adapters implement these protocols.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM providers (Adapter Pattern)."""

    async def agenerate(self, messages: list[dict]) -> str: ...

    @property
    def provider_name(self) -> str: ...

    @property
    def model_name(self) -> str: ...


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector database adapters."""

    def upsert_vectors(
        self,
        ids: list[str],
        vectors: list[list[float]],
        metadatas: list[dict],
        namespace: str = "",
        batch_size: int = 100,
    ) -> int: ...

    def query(
        self,
        vector: list[float],
        top_k: int = 10,
        namespace: str = "",
        filter: dict | None = None,
        include_metadata: bool = True,
    ) -> list[dict]: ...


@runtime_checkable
class Embedder(Protocol):
    """Protocol for embedding providers."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...

    @property
    def dimension(self) -> int: ...


@runtime_checkable
class Reranker(Protocol):
    """Protocol for reranking strategies (Strategy Pattern)."""

    def rerank(self, query: str, chunks: list[dict], top_k: int = 4) -> list[dict]: ...


@runtime_checkable
class ConversationMemory(Protocol):
    """Protocol for conversation storage."""

    def add_message(self, conversation_id: str, role: str, content: str) -> None: ...

    def get_history(self, conversation_id: str, max_turns: int = 10) -> list[dict]: ...

    def clear(self, conversation_id: str) -> None: ...
