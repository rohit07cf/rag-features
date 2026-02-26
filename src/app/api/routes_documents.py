"""Document upload endpoint — thin route delegates to IngestionService."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session

from src.app.api.schemas import UploadResponse
from src.app.deps import get_db
from src.domain.models.errors import NotFoundError, ValidationError
from src.domain.services.ingestion_service import IngestionService

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.post("/upload", response_model=list[UploadResponse])
async def upload_documents(
    assistant_id: str = Form(...),
    user_id: str = Form("demo_user"),
    chunk_strategy: str = Form("recursive"),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload documents and start ingestion workflows."""
    service = IngestionService(db)

    try:
        service.validate_upload(assistant_id, [f.filename or "file" for f in files])
    except NotFoundError as e:
        raise HTTPException(404, e.message)
    except ValidationError as e:
        raise HTTPException(400, e.message)

    # Read file contents
    file_data = []
    for f in files:
        content = await f.read()
        file_data.append((f.filename or "unknown", content))

    results = await service.save_and_ingest(
        assistant_id=assistant_id,
        user_id=user_id,
        chunk_strategy=chunk_strategy,
        files=file_data,
    )

    return [UploadResponse(**r) for r in results]
