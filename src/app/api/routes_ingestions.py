"""Ingestion status endpoint — thin route delegates to IngestionService."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from src.app.api.schemas import IngestionStatusResponse
from src.app.deps import get_db
from src.app.domain.models.errors import NotFoundError
from src.app.domain.services.ingestion_service import IngestionService

router = APIRouter(prefix="/v1/ingestions", tags=["ingestions"])


@router.get("/{ingestion_id}/status", response_model=IngestionStatusResponse)
def get_ingestion_status(ingestion_id: str, db: Session = Depends(get_db)):
    """Return current state and progress of an ingestion workflow."""
    service = IngestionService(db)
    try:
        result = service.get_ingestion_status(ingestion_id)
    except NotFoundError as e:
        raise HTTPException(404, e.message)

    return IngestionStatusResponse(**result)
