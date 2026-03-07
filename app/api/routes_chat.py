"""Chat endpoint — thin route layer delegates to ChatService (Facade Pattern).

This endpoint powers the RAG chat experience:

Real-Time RAG Chat Flow:
1. User sends message to /v1/chat
2. System checks assistant type (model_only vs rag)
3. For RAG assistants:
   - Retrieve relevant document chunks
   - Build prompt with context + citations
   - LLM generates answer using your documents
   - Return response with source references
4. For model-only: Direct LLM call (no documents)

Example Request:
POST /v1/chat
{
  "assistant_id": "hr-assistant",
  "message": "What's the vacation policy?",
  "conversation_id": "conv_123"
}

Response includes answer + citations like:
"Employees get 15 vacation days annually [Source 1, p.12]"

All business logic (memory, retrieval, prompt building, LLM call) lives
in ChatService. The route only orchestrates: parse → get deps → call service.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.api.schemas import ChatRequest, ChatResponse
from app.container import get_chat_service, get_llm
from app.deps import get_db
from app.storage import assistants_repo

router = APIRouter(prefix="/v1", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, db: Session = Depends(get_db)):
    """Unified chat endpoint — dispatches to model-only or RAG via ChatService.

    Real-time decision logic:
    - assistant.type == "model_only": Basic chat (LLM training data only)
    - assistant.type == "rag": Smart chat (LLM + your documents)

    Both return same ChatResponse format for consistent API.
    """
    assistant = assistants_repo.get_assistant(db, body.assistant_id)
    if not assistant:
        raise HTTPException(404, "Assistant not found")

    llm = get_llm(provider=assistant.provider, model=assistant.model)
    service = get_chat_service()

    try:
        if assistant.type == "model_only":
            # Basic chat: LLM responds using only training data
            # Good for: General questions, creative tasks
            # Bad for: Company-specific or factual questions
            return await service.chat_model_only(
                llm=llm,
                message=body.message,
                system_prompt=assistant.system_prompt or "",
                conversation_id=body.conversation_id,
            )
        else:
            # RAG chat: LLM gets relevant document context first
            # Good for: Answering from your knowledge base
            # Provides: Factual answers + source citations
            return await service.chat_rag(
                llm=llm,
                message=body.message,
                assistant_id=assistant.id,
                system_prompt=assistant.system_prompt or "",
                conversation_id=body.conversation_id,
            )
    except Exception as exc:
        error_text = str(exc).lower()
        if "not_found_error" in error_text and "model:" in error_text:
            logger.warning("Provider model unavailable for assistant %s: %s", assistant.id, exc)
            raise HTTPException(
                status_code=502,
                detail=(
                    "The configured model is unavailable for the current provider/API key. "
                    "Please choose a different model for this assistant."
                ),
            ) from exc
        raise
