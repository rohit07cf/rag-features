"""Assistants CRUD endpoints — thin route layer.

Validation is handled by Pydantic enums in schemas (AssistantType, LLMProvider).
Routes only orchestrate: parse request → delegate to repo → return response.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.api.schemas import AssistantCreate, AssistantResponse, RagStatusResponse
from app.deps import get_db
from app.storage import assistants_repo

router = APIRouter(prefix="/v1/assistants", tags=["assistants"])


@router.post("", response_model=AssistantResponse, status_code=201)
def create_assistant(body: AssistantCreate, db: Session = Depends(get_db)):
    # Pydantic enum validation on AssistantCreate handles type/provider checks.
    assistant = assistants_repo.create_assistant(db, **body.model_dump(mode="json"))
    return assistant


@router.get("", response_model=list[AssistantResponse])
def list_assistants(user_id: str, db: Session = Depends(get_db)):
    return assistants_repo.list_assistants(db, user_id)


@router.get("/{assistant_id}", response_model=AssistantResponse)
def get_assistant(assistant_id: str, db: Session = Depends(get_db)):
    assistant = assistants_repo.get_assistant(db, assistant_id)
    if not assistant:
        raise HTTPException(404, "Assistant not found")
    return assistant


@router.get("/{assistant_id}/rag_status", response_model=RagStatusResponse)
def rag_status(assistant_id: str, db: Session = Depends(get_db)):
    assistant = assistants_repo.get_assistant(db, assistant_id)
    if not assistant:
        raise HTTPException(404, "Assistant not found")
    return assistants_repo.get_rag_status(db, assistant_id)
