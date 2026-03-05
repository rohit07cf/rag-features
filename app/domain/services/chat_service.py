"""Chat service — Facade pattern.

Hides the complexity of model-only vs RAG chat behind a clean interface.
Consumes domain protocols, not concrete implementations.
"""

from __future__ import annotations

import uuid

from app.api.schemas import ChatResponse, SourceReference
from app.domain.pipelines.retrieval_pipeline import RetrievalPipeline
from app.domain.protocols import ConversationMemory, LLMClient
from app.rag.prompts.templates import build_rag_prompt


class ChatService:
    """Facade for all chat operations.

    Routes call chat_model_only() or chat_rag() — the service
    handles LLM calls, retrieval, memory, and response formatting.
    """

    def __init__(
        self,
        memory: ConversationMemory,
        retrieval_pipeline: RetrievalPipeline | None = None,
    ):
        self._memory = memory
        self._pipeline = retrieval_pipeline

    async def chat_model_only(
        self,
        llm: LLMClient,
        message: str,
        system_prompt: str = "",
        conversation_id: str | None = None,
    ) -> ChatResponse:
        """Direct LLM call without retrieval."""
        conversation_id = conversation_id or uuid.uuid4().hex[:16]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        history = self._memory.get_history(conversation_id)
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        answer = await llm.agenerate(messages)

        self._memory.add_message(conversation_id, "user", message)
        self._memory.add_message(conversation_id, "assistant", answer)

        return ChatResponse(
            answer=answer,
            conversation_id=conversation_id,
            sources=[],
            model_used=llm.model_name,
            provider=llm.provider_name,
        )

    async def chat_rag(
        self,
        llm: LLMClient,
        message: str,
        assistant_id: str,
        system_prompt: str = "",
        conversation_id: str | None = None,
    ) -> ChatResponse:
        """Retrieval-augmented generation with reranking and citations."""
        if self._pipeline is None:
            raise RuntimeError("RetrievalPipeline not configured for RAG chat")

        conversation_id = conversation_id or uuid.uuid4().hex[:16]

        # Stage 1: Retrieve relevant chunks
        chunks = await self._pipeline.run(
            query=message,
            assistant_id=assistant_id,
            top_k=8,
            rerank_top_k=4,
        )

        # Stage 2: Build prompt with context
        history = self._memory.get_history(conversation_id)
        messages = build_rag_prompt(
            query=message,
            chunks=chunks,
            system_prompt=system_prompt,
            history=history,
        )

        # Stage 3: Generate
        answer = await llm.agenerate(messages)

        # Stage 4: Store in memory
        self._memory.add_message(conversation_id, "user", message)
        self._memory.add_message(conversation_id, "assistant", answer)

        # Stage 5: Format sources
        sources = [
            SourceReference(
                document_id=c.get("document_id", ""),
                chunk_id=c.get("chunk_id", ""),
                text_snippet=c.get("text", "")[:200],
                score=c.get("score", 0.0),
                page_numbers=c.get("page_numbers", []),
                heading_path=c.get("heading_path", []),
            )
            for c in chunks
        ]

        return ChatResponse(
            answer=answer,
            conversation_id=conversation_id,
            sources=sources,
            model_used=llm.model_name,
            provider=llm.provider_name,
        )
