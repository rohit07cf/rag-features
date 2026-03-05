"""Repository helpers for Assistants and IngestionRecords."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from src.app.storage.models import Assistant, IngestionRecord


# ── Assistants ────────────────────────────────────────────────────


def create_assistant(session: Session, **kwargs) -> Assistant:
    assistant = Assistant(**kwargs)
    session.add(assistant)
    session.commit()
    session.refresh(assistant)
    return assistant


def get_assistant(session: Session, assistant_id: str) -> Optional[Assistant]:
    return session.get(Assistant, assistant_id)


def list_assistants(session: Session, user_id: str) -> list[Assistant]:
    stmt = (
        select(Assistant).where(Assistant.user_id == user_id).order_by(Assistant.created_at.desc())
    )
    return list(session.exec(stmt).all())


# ── Ingestion Records ────────────────────────────────────────────


def create_ingestion_record(session: Session, **kwargs) -> IngestionRecord:
    record = IngestionRecord(**kwargs)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_ingestion_record(session: Session, record_id: str) -> Optional[IngestionRecord]:
    return session.get(IngestionRecord, record_id)


def update_ingestion_state(
    session: Session,
    record_id: str,
    *,
    state: Optional[str] = None,
    current_step: Optional[str] = None,
    progress_pct: Optional[int] = None,
    error_message: Optional[str] = None,
) -> Optional[IngestionRecord]:
    record = session.get(IngestionRecord, record_id)
    if not record:
        return None
    if state is not None:
        record.state = state
    if current_step is not None:
        record.current_step = current_step
    if progress_pct is not None:
        record.progress_pct = progress_pct
    if error_message is not None:
        record.error_message = error_message
    record.updated_at = datetime.now(timezone.utc)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def list_ingestion_records(
    session: Session,
    assistant_id: str,
) -> list[IngestionRecord]:
    stmt = (
        select(IngestionRecord)
        .where(IngestionRecord.assistant_id == assistant_id)
        .order_by(IngestionRecord.created_at.desc())
    )
    return list(session.exec(stmt).all())


def get_rag_status(session: Session, assistant_id: str) -> dict:
    """Return RAG readiness info for an assistant."""
    records = list_ingestion_records(session, assistant_id)
    succeeded = [r for r in records if r.state == "succeeded"]
    last_state = records[0].state if records else None
    return {
        "has_documents": len(succeeded) > 0,
        "num_docs": len(succeeded),
        "total_ingestions": len(records),
        "last_ingestion_state": last_state,
    }
