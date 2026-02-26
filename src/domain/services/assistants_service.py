"""Assistants service — thin wrapper around repo with domain validation."""

from __future__ import annotations

from sqlmodel import Session

from src.app.storage import assistants_repo
from src.domain.models.errors import NotFoundError


class AssistantsService:
    """Domain service for assistant CRUD operations."""

    def __init__(self, db: Session):
        self._db = db

    def create(self, **kwargs) -> dict:
        assistant = assistants_repo.create_assistant(self._db, **kwargs)
        return assistant

    def get(self, assistant_id: str):
        assistant = assistants_repo.get_assistant(self._db, assistant_id)
        if not assistant:
            raise NotFoundError("Assistant not found", details=f"id={assistant_id}")
        return assistant

    def list_for_user(self, user_id: str) -> list:
        return assistants_repo.list_assistants(self._db, user_id)

    def get_rag_status(self, assistant_id: str) -> dict:
        # Ensure assistant exists first
        self.get(assistant_id)
        return assistants_repo.get_rag_status(self._db, assistant_id)
