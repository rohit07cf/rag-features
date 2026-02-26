"""Document upload endpoint — triggers Temporal ingestion workflow."""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session

from src.app.api.schemas import UploadResponse
from src.app.deps import get_db
from src.app.logging import get_logger
from src.app.settings import get_settings
from src.app.storage import assistants_repo

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.post("/upload", response_model=list[UploadResponse])
async def upload_documents(
    assistant_id: str = Form(...),
    user_id: str = Form("demo_user"),
    chunk_strategy: str = Form("recursive"),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload one or more documents and start ingestion workflows."""
    assistant = assistants_repo.get_assistant(db, assistant_id)
    if not assistant:
        raise HTTPException(404, "Assistant not found")
    if assistant.type != "rag":
        raise HTTPException(400, "Assistant is not a RAG assistant")

    settings = get_settings()
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)

    results: list[UploadResponse] = []

    for f in files:
        ext = os.path.splitext(f.filename or "file")[1].lower()
        if ext not in (".pdf", ".docx", ".txt"):
            raise HTTPException(400, f"Unsupported file type: {ext}")

        doc_id = uuid.uuid4().hex[:12]
        file_path = os.path.join(upload_dir, f"{doc_id}{ext}")

        content = await f.read()
        with open(file_path, "wb") as fh:
            fh.write(content)

        # Create ingestion record
        record = assistants_repo.create_ingestion_record(
            db,
            assistant_id=assistant_id,
            user_id=user_id,
            document_id=doc_id,
            filename=f.filename or "unknown",
            state="pending",
        )

        # Start Temporal workflow (best-effort; if Temporal is down, record stays pending)
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
                db, record.id, state="running", workflow_id=wf_id
            )
            record.workflow_id = wf_id
        except Exception as exc:
            logger.warning("Temporal workflow start failed: %s — marking running anyway", exc)
            assistants_repo.update_ingestion_state(db, record.id, state="running")

        results.append(
            UploadResponse(
                document_id=doc_id,
                ingestion_id=record.id,
                filename=f.filename or "unknown",
                status=record.state,
            )
        )

    return results
