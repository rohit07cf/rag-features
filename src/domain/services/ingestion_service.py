"""Ingestion service — orchestrates document upload and workflow trigger."""

from __future__ import annotations

import os
import uuid

from sqlmodel import Session

from src.app.logging import get_logger
from src.app.settings import get_settings
from src.app.storage import assistants_repo
from src.domain.models.errors import NotFoundError, ValidationError

logger = get_logger(__name__)


class IngestionService:
    """Handles file persistence and ingestion workflow dispatch."""

    def __init__(self, db: Session):
        self._db = db
        self._settings = get_settings()

    def validate_upload(self, assistant_id: str, filenames: list[str]) -> None:
        """Validate assistant exists, is RAG, and files are supported."""
        assistant = assistants_repo.get_assistant(self._db, assistant_id)
        if not assistant:
            raise NotFoundError("Assistant not found", details=f"id={assistant_id}")
        if assistant.type != "rag":
            raise ValidationError("Assistant is not a RAG assistant")

        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in (".pdf", ".docx", ".txt"):
                raise ValidationError(f"Unsupported file type: {ext}")

    async def save_and_ingest(
        self,
        assistant_id: str,
        user_id: str,
        chunk_strategy: str,
        files: list[tuple[str, bytes]],
    ) -> list[dict]:
        """Save files to disk and start ingestion workflows.

        Returns:
            List of {document_id, ingestion_id, filename, status} dicts.
        """
        upload_dir = self._settings.upload_dir
        os.makedirs(upload_dir, exist_ok=True)

        results: list[dict] = []

        for filename, content in files:
            ext = os.path.splitext(filename)[1].lower()
            doc_id = uuid.uuid4().hex[:12]
            file_path = os.path.join(upload_dir, f"{doc_id}{ext}")

            with open(file_path, "wb") as fh:
                fh.write(content)

            record = assistants_repo.create_ingestion_record(
                self._db,
                assistant_id=assistant_id,
                user_id=user_id,
                document_id=doc_id,
                filename=filename,
                state="pending",
            )

            # Start Temporal workflow (best-effort)
            try:
                from src.workflows.temporal_client import start_ingestion_workflow

                wf_id = await start_ingestion_workflow(
                    ingestion_id=record.id,
                    document_id=doc_id,
                    file_path=file_path,
                    chunk_strategy=chunk_strategy,
                    assistant_id=assistant_id,
                    user_id=user_id,
                )
                assistants_repo.update_ingestion_state(
                    self._db, record.id, state="running", workflow_id=wf_id
                )
                record.workflow_id = wf_id
            except Exception as exc:
                logger.warning("Temporal workflow start failed: %s — marking running", exc)
                assistants_repo.update_ingestion_state(self._db, record.id, state="running")

            results.append({
                "document_id": doc_id,
                "ingestion_id": record.id,
                "filename": filename,
                "status": record.state,
            })

        return results

    def get_ingestion_status(self, ingestion_id: str) -> dict:
        """Get ingestion progress from DB."""
        record = assistants_repo.get_ingestion_record(self._db, ingestion_id)
        if not record:
            raise NotFoundError("Ingestion record not found")

        return {
            "ingestion_id": record.id,
            "state": record.state,
            "current_step": record.current_step,
            "progress_pct": record.progress_pct,
            "error_message": record.error_message,
        }
