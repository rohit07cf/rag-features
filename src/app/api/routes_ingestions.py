"""Ingestion status endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from src.app.api.schemas import IngestionStatusResponse
from src.app.deps import get_db
from src.app.storage import assistants_repo

router = APIRouter(prefix="/v1/ingestions", tags=["ingestions"])


@router.get("/{ingestion_id}/status", response_model=IngestionStatusResponse)
def get_ingestion_status(ingestion_id: str, db: Session = Depends(get_db)):
    """Return current state and progress of an ingestion workflow."""
    record = assistants_repo.get_ingestion_record(db, ingestion_id)
    if not record:
        raise HTTPException(404, "Ingestion record not found")

    # Try to query Temporal for live progress (best-effort)
    try:
        from src.workflows.temporal_client import query_ingestion_progress

        import asyncio

        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside an async context already — just return DB state
            pass
        else:
            progress = loop.run_until_complete(
                query_ingestion_progress(record.workflow_id)
            )
            if progress:
                record.current_step = progress.get("current_step", record.current_step)
                record.progress_pct = progress.get("progress_pct", record.progress_pct)
    except Exception:
        pass  # Temporal may be unavailable; fall back to DB state

    return IngestionStatusResponse(
        ingestion_id=record.id,
        state=record.state,
        current_step=record.current_step,
        progress_pct=record.progress_pct,
        error_message=record.error_message,
    )
