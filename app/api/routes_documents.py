"""Document upload endpoint — thin route delegates to IngestionService.

Supports multifile uploads with configurable size validation:
- Multiple files: Up to N files per request
- Size limit: Configurable via settings (default: 50MB per file)
- Validation: Checked before processing to fail fast

Real-time upload flow:
1. User selects multiple files (PDFs, Word docs, etc.)
2. System validates file sizes (reject > configured limit)
3. Files saved to temp storage
4. Temporal workflows process each file
5. Progress tracked via ingestion IDs
"""

from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session
from typing import List

from app.api.schemas import UploadResponse
from app.deps import get_db
from app.domain.models.errors import NotFoundError, ValidationError
from app.domain.services.ingestion_service import IngestionService
from app.settings import get_settings

router = APIRouter(prefix="/v1/documents", tags=["documents"])

# File size limits
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
MAX_FILE_SIZE_MB = 50


@router.post(
    "/upload",
    response_model=list[UploadResponse],
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["assistant_id", "files"],
                        "properties": {
                            "assistant_id": {"type": "string"},
                            "user_id": {"type": "string", "default": "demo_user"},
                            "chunk_strategy": {"type": "string", "default": "recursive"},
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                            },
                        },
                    }
                }
            },
            "required": True,
        }
    },
)
async def upload_documents(
    assistant_id: str = Form(..., description="ID of the RAG assistant to upload documents to"),
    user_id: str = Form("demo_user", description="User identifier for tracking"),
    chunk_strategy: str = Form(
        "recursive",
        description="Text chunking strategy: recursive, token, heading_aware, adaptive, contextual_docintel",
    ),
    files: Annotated[List[UploadFile], File(description="Multiddple PDF/DOCX/TXT files. Max 50MB each.")] = ...,
    db: Session = Depends(get_db),
    settings=Depends(get_settings),
):
    """Upload multiple documents and start ingestion workflows.

    **Supported File Types:**
    - **PDF** (.pdf) - `application/pdf`
    - **Word** (.docx) - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
    - **Text** (.txt) - `text/plain`

    **Features:**
    - Multiple file upload in single request
    - Automatic file type validation
    - Size limit: 50MB per file (configurable)
    - Asynchronous processing via Temporal workflows
    - Real-time progress tracking

    **Process:**
    1. Validate files (type, size, assistant permissions)
    2. Save files to temporary storage
    3. Start ingestion workflows (extract → clean → chunk → embed → store)
    4. Return ingestion IDs for progress monitoring

    Returns list of upload results with document IDs and ingestion tracking info.
    """
    service = IngestionService(db)

    # Get file size limit from settings (default: 50MB)
    max_file_size = settings.max_upload_size_mb * 1024 * 1024  # Convert MB to bytes

    # Validate assistant exists and file types
    try:
        service.validate_upload(assistant_id, [f.filename or "file" for f in files])
    except NotFoundError as e:
        raise HTTPException(404, e.message)
    except ValidationError as e:
        raise HTTPException(400, e.message)

    # Validate file sizes (using configured limit)
    for file in files:
        # Get file size from Content-Length header or seek to end
        file_size = getattr(file, "size", None)
        if file_size is None:
            # Fallback: try to get size by seeking
            try:
                await file.seek(0, 2)  # Seek to end
                file_size = await file.tell()
                await file.seek(0)  # Reset to beginning
            except Exception:
                # If we can't determine size, allow it (will be caught during read)
                continue

        if file_size and file_size > max_file_size:
            raise HTTPException(
                413,  # Request Entity Too Large
                f"File '{file.filename}' exceeds {settings.max_upload_size_mb}MB limit "
                f"({file_size / (1024*1024):.1f}MB actual size)",
            )

    # Read file contents (now safe after size validation)
    file_data = []
    for f in files:
        try:
            content = await f.read()
            # Double-check size after reading (in case header was wrong)
            if len(content) > max_file_size:
                raise HTTPException(
                    413,
                    f"File '{f.filename}' exceeds {settings.max_upload_size_mb}MB limit after reading",
                )
            file_data.append((f.filename or "unknown", content))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, f"Error reading file '{f.filename}': {str(e)}")

    # Start ingestion workflows
    results = await service.save_and_ingest(
        assistant_id=assistant_id,
        user_id=user_id,
        chunk_strategy=chunk_strategy,
        files=file_data,
    )

    return [UploadResponse(**r) for r in results]
