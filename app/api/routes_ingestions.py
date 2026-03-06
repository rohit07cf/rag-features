"""Ingestion status endpoint — queries Temporal workflow for live progress."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.api.schemas import IngestionStatusResponse
from app.deps import get_db
from app.domain.models.errors import NotFoundError
from app.domain.services.ingestion_service import IngestionService

router = APIRouter(prefix="/v1/ingestions", tags=["ingestions"])


@router.get("/{ingestion_id}/status", response_model=IngestionStatusResponse)
async def get_ingestion_status(ingestion_id: str, db: Session = Depends(get_db)):
    """Return current state and progress of an ingestion workflow.

    Queries the Temporal workflow directly for live progress, falling back
    to the DB record if the workflow is unreachable.
    """
    service = IngestionService(db)
    try:
        db_status = service.get_ingestion_status(ingestion_id)
    except NotFoundError as e:
        raise HTTPException(404, e.message)

    # If we have a workflow_id, query Temporal for live progress
    workflow_id = db_status.get("workflow_id")
    if workflow_id:
        try:
            from app.workflows.temporal_client import query_ingestion_progress

            progress = await query_ingestion_progress(workflow_id)
            if progress:
                db_status["current_step"] = progress.get("current_step", db_status.get("current_step"))
                db_status["progress_pct"] = progress.get("progress_pct", db_status.get("progress_pct"))
                # Sync terminal states back
                if progress.get("current_step") in ("succeeded", "failed"):
                    db_status["state"] = progress["current_step"]
        except Exception:
            pass  # Fall back to DB values

    return IngestionStatusResponse(**db_status)
