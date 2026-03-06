"""Ingestion service — orchestrates document upload and workflow trigger."""

from __future__ import annotations

import base64
import os
import uuid

from sqlmodel import Session

from app.logging import get_logger
from app.settings import get_settings
from app.storage import assistants_repo
from app.domain.models.errors import NotFoundError, ValidationError

logger = get_logger(__name__)


class IngestionService:
    """Handles file persistence and ingestion workflow dispatch."""

    def __init__(self, db: Session):
        self._db = db
        self._settings = get_settings()

    def validate_upload(self, assistant_id: str, filenames: list[str]) -> None:
        """Validate assistant exists, is RAG, and files are supported.

        Supported formats:
        - PDF (.pdf) - Portable Document Format
        - DOCX (.docx) - Microsoft Word Open XML
        - TXT (.txt) - Plain text files
        """
        assistant = assistants_repo.get_assistant(self._db, assistant_id)
        if not assistant:
            raise NotFoundError("Assistant not found", details=f"id={assistant_id}")
        if assistant.type != "rag":
            raise ValidationError(
                "Assistant is not a RAG assistant",
                details="Only RAG assistants can process documents. Create a RAG assistant first.",
            )

        # Supported file extensions and their descriptions
        supported_types = {
            ".pdf": "PDF documents",
            ".docx": "Word documents (.docx)",
            ".txt": "Plain text files",
        }

        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in supported_types:
                supported_list = ", ".join(
                    f"{ext} ({desc})" for ext, desc in supported_types.items()
                )
                raise ValidationError(
                    f"Unsupported file type: {ext}",
                    details=f"Supported formats: {supported_list}. File: {fname}",
                )

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
        results: list[dict] = []

        for filename, content in files:
            doc_id = uuid.uuid4().hex[:12]

            # Encode file content as base64 to pass through Temporal
            # (worker runs in a separate container with no shared filesystem)
            file_content_b64 = base64.b64encode(content).decode("ascii")

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
                from app.workflows.temporal_client import start_ingestion_workflow

                wf_id = await start_ingestion_workflow(
                    ingestion_id=record.id,
                    document_id=doc_id,
                    filename=filename,
                    file_content_b64=file_content_b64,
                    chunk_strategy=chunk_strategy,
                    assistant_id=assistant_id,
                    user_id=user_id,
                )
                record.workflow_id = wf_id
                self._db.add(record)
                self._db.commit()
                assistants_repo.update_ingestion_state(
                    self._db, record.id, state="running"
                )
            except Exception as exc:
                logger.warning("Temporal workflow start failed: %s — marking running", exc)
                assistants_repo.update_ingestion_state(self._db, record.id, state="running")

            results.append(
                {
                    "document_id": doc_id,
                    "ingestion_id": record.id,
                    "filename": filename,
                    "status": record.state,
                }
            )

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
            "workflow_id": record.workflow_id,
        }
