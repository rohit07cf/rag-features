"""Composition Root — wires all dependencies in one place.

This is the single location where infrastructure implementations
are bound to domain protocols. No other module should instantiate
external clients directly.
"""

from __future__ import annotations

from functools import lru_cache


@lru_cache
def get_memory():
    """Singleton in-memory conversation store."""
    from src.app.rag.memory.in_memory import InMemoryStore

    return InMemoryStore()


def get_embedder():
    """Create an embedder instance."""
    from src.app.rag.embeddings.openai_embedder import OpenAIEmbedder

    return OpenAIEmbedder()


def get_vector_store():
    """Create a vector store instance."""
    from src.app.rag.vectorstore.pinecone_store import PineconeStore

    return PineconeStore()


def get_reranker():
    """Create a reranker instance."""
    from src.app.rag.retrieval.rerank.local_reranker import LocalReranker

    return LocalReranker()


def get_retrieval_pipeline():
    """Assemble the retrieval pipeline with all dependencies."""
    from src.app.domain.pipelines.retrieval_pipeline import RetrievalPipeline

    return RetrievalPipeline(
        embedder=get_embedder(),
        vector_store=get_vector_store(),
        reranker=get_reranker(),
    )


def get_chat_service():
    """Assemble the chat service facade."""
    from src.app.domain.services.chat_service import ChatService

    return ChatService(
        memory=get_memory(),
        retrieval_pipeline=get_retrieval_pipeline(),
    )


def get_llm(provider: str, model: str):
    """Factory method for LLM clients."""
    from src.app.rag.llms.factory import create_llm

    return create_llm(provider=provider, model=model)
