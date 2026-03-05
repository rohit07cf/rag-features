"""Chat endpoint — thin route layer delegates to ChatService (Facade Pattern).

All business logic (memory, retrieval, prompt building, LLM call) lives
in ChatService. The route only orchestrates: parse → get deps → call service.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.api.schemas import ChatRequest, ChatResponse
from app.container import get_chat_service, get_llm
from app.deps import get_db
from app.storage import assistants_repo

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, db: Session = Depends(get_db)):
    """Unified chat endpoint — dispatches to model-only or RAG via ChatService."""
    assistant = assistants_repo.get_assistant(db, body.assistant_id)
    if not assistant:
        raise HTTPException(404, "Assistant not found")

    llm = get_llm(provider=assistant.provider, model=assistant.model)
    service = get_chat_service()

    if assistant.type == "model_only":
        return await service.chat_model_only(
            llm=llm,
            message=body.message,
            system_prompt=assistant.system_prompt or "",
            conversation_id=body.conversation_id,
        )
    else:
        return await service.chat_rag(
            llm=llm,
            message=body.message,
            assistant_id=assistant.id,
            system_prompt=assistant.system_prompt or "",
            conversation_id=body.conversation_id,
        )
