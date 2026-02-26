"""Chat endpoints — routes model-only vs RAG based on assistant type."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from src.app.api.schemas import ChatRequest, ChatResponse, SourceReference
from src.app.deps import get_db
from src.app.logging import get_logger
from src.app.storage import assistants_repo

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, db: Session = Depends(get_db)):
    """Unified chat endpoint — dispatches to model-only or RAG path."""
    assistant = assistants_repo.get_assistant(db, body.assistant_id)
    if not assistant:
        raise HTTPException(404, "Assistant not found")

    conversation_id = body.conversation_id or uuid.uuid4().hex[:16]

    if assistant.type == "model_only":
        return await _model_only_chat(assistant, body, conversation_id)
    else:
        return await _rag_chat(assistant, body, conversation_id)


async def _model_only_chat(assistant, body: ChatRequest, conversation_id: str) -> ChatResponse:
    """Direct LLM call without retrieval."""
    from src.rag.llms.factory import create_llm
    from src.rag.memory.in_memory import InMemoryStore

    llm = create_llm(provider=assistant.provider, model=assistant.model)
    memory = InMemoryStore()

    # Build messages
    messages = []
    if assistant.system_prompt:
        messages.append({"role": "system", "content": assistant.system_prompt})

    # Add conversation history
    history = memory.get_history(conversation_id)
    messages.extend(history)
    messages.append({"role": "user", "content": body.message})

    answer = await llm.agenerate(messages)

    # Save to memory
    memory.add_message(conversation_id, "user", body.message)
    memory.add_message(conversation_id, "assistant", answer)

    return ChatResponse(
        answer=answer,
        conversation_id=conversation_id,
        sources=[],
        model_used=assistant.model,
        provider=assistant.provider,
    )


async def _rag_chat(assistant, body: ChatRequest, conversation_id: str) -> ChatResponse:
    """Retrieval-augmented generation with reranking and citations."""
    from src.rag.llms.factory import create_llm
    from src.rag.memory.in_memory import InMemoryStore
    from src.rag.prompts.templates import build_rag_prompt
    from src.rag.retrieval.retriever import retrieve_and_rerank

    llm = create_llm(provider=assistant.provider, model=assistant.model)
    memory = InMemoryStore()

    # Retrieve relevant chunks
    chunks = await retrieve_and_rerank(
        query=body.message,
        assistant_id=assistant.id,
        top_k=8,
        rerank_top_k=4,
    )

    # Build context + prompt
    history = memory.get_history(conversation_id)
    system_prompt = assistant.system_prompt or ""
    messages = build_rag_prompt(
        query=body.message,
        chunks=chunks,
        system_prompt=system_prompt,
        history=history,
    )

    answer = await llm.agenerate(messages)

    # Save to memory
    memory.add_message(conversation_id, "user", body.message)
    memory.add_message(conversation_id, "assistant", answer)

    # Build source references
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
        model_used=assistant.model,
        provider=assistant.provider,
    )
