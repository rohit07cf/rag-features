"""Chat service — Facade pattern.

This service demonstrates the two main approaches to LLM conversations:

1. Model-Only Chat: Direct LLM call (basic, may hallucinate)
2. RAG Chat: Retrieval-Augmented Generation (factual, cited answers)

RAG enhances LLM responses by providing relevant context from documents,
reducing hallucinations and enabling source citations.

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

    Real-Time RAG Conversation Flow:
    1. User: "What are the environmental benefits of solar power?"
    2. System retrieves relevant document chunks about solar energy
    3. LLM receives: [Context about solar benefits] + [User question]
    4. LLM generates: "Solar power reduces CO2 emissions by X% [Source 1, p.5]"
    5. Response includes citations for verification

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
        """Direct LLM call without retrieval.

        This is traditional chat - LLM responds based only on training data.
        Good for: General questions, creative tasks, when no documents available.
        Bad for: Factual questions requiring up-to-date or specific knowledge.

        Real-time example: "Write a haiku about cats"
        → LLM generates poem from training data (no external knowledge needed)
        """
        conversation_id = conversation_id or uuid.uuid4().hex[:16]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Include conversation history for context
        history = self._memory.get_history(conversation_id)
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        # LLM generates response using only its training data
        answer = await llm.agenerate(messages)

        # Store conversation in memory for continuity
        self._memory.add_message(conversation_id, "user", message)
        self._memory.add_message(conversation_id, "assistant", answer)

        return ChatResponse(
            answer=answer,
            conversation_id=conversation_id,
            sources=[],  # No sources for model-only chat
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
        """Retrieval-augmented generation with reranking and citations.

        This is the advanced approach that makes LLMs "knowledgeable" about your documents.

        Real-Time RAG Process:
        1. User asks question
        2. System searches document database for relevant chunks
        3. LLM receives question + relevant context from your documents
        4. LLM generates answer using provided facts + includes citations
        5. User gets accurate, verifiable answers from their knowledge base

        Example: "What is our company policy on remote work?"
        → Retrieves relevant HR policy chunks
        → LLM answers using actual policy text + cites source document
        """
        if self._pipeline is None:
            raise RuntimeError("RetrievalPipeline not configured for RAG chat")

        conversation_id = conversation_id or uuid.uuid4().hex[:16]

        # Stage 1: Retrieve relevant chunks from knowledge base
        # This finds the most relevant parts of your documents
        chunks = await self._pipeline.run(
            query=message,
            assistant_id=assistant_id,
            top_k=8,  # Get 8 candidate chunks
            rerank_top_k=4,  # Keep top 4 after reranking
        )

        # Stage 2: Build prompt with retrieved context
        # Formats chunks + conversation history into LLM prompt
        history = self._memory.get_history(conversation_id)
        messages = build_rag_prompt(
            query=message,
            chunks=chunks,
            system_prompt=system_prompt,
            history=history,
        )

        # Stage 3: Generate answer using retrieved context
        # LLM now has access to your document knowledge
        answer = await llm.agenerate(messages)

        # Stage 4: Store conversation for future context
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
