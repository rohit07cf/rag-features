"""Temporal workflow for durable document ingestion.

Pipeline: extract -> clean -> chunk -> embed batches -> upsert Pinecone
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from src.app.workflows.activities.chunk_text import chunk_text
    from src.app.workflows.activities.clean_text import clean_text
    from src.app.workflows.activities.embed_batches import embed_batches
    from src.app.workflows.activities.extract_text import extract_text
    from src.app.workflows.activities.upsert_pinecone import upsert_pinecone


@workflow.defn
class IngestionWorkflow:
    """Durable ingestion: extract → clean → chunk → embed → upsert."""

    def __init__(self) -> None:
        self._progress = {"current_step": "pending", "progress_pct": 0}

    @workflow.query(name="get_progress")
    def get_progress(self) -> dict:
        return self._progress

    @workflow.run
    async def run(self, params: dict[str, Any]) -> dict:
        ingestion_id = params["ingestion_id"]
        document_id = params["document_id"]
        file_path = params["file_path"]
        chunk_strategy = params["chunk_strategy"]
        assistant_id = params["assistant_id"]
        _user_id = params["user_id"]

        activity_timeout = timedelta(minutes=10)

        try:
            # Step 1: Extract text
            self._progress = {"current_step": "extracting", "progress_pct": 10}
            raw_text = await workflow.execute_activity(
                extract_text,
                {"file_path": file_path, "document_id": document_id},
                start_to_close_timeout=activity_timeout,
            )

            # Step 2: Clean text
            self._progress = {"current_step": "cleaning", "progress_pct": 25}
            cleaned_text = await workflow.execute_activity(
                clean_text,
                {"text": raw_text, "document_id": document_id},
                start_to_close_timeout=activity_timeout,
            )

            # Step 3: Chunk text
            self._progress = {"current_step": "chunking", "progress_pct": 40}
            chunks = await workflow.execute_activity(
                chunk_text,
                {
                    "text": cleaned_text,
                    "document_id": document_id,
                    "strategy": chunk_strategy,
                    "file_path": file_path,
                },
                start_to_close_timeout=activity_timeout,
            )

            # Step 4: Embed batches
            self._progress = {"current_step": "embedding", "progress_pct": 60}
            embedded_chunks = await workflow.execute_activity(
                embed_batches,
                {"chunks": chunks, "document_id": document_id},
                start_to_close_timeout=activity_timeout,
            )

            # Step 5: Upsert to Pinecone
            self._progress = {"current_step": "upserting", "progress_pct": 80}
            result = await workflow.execute_activity(
                upsert_pinecone,
                {
                    "embedded_chunks": embedded_chunks,
                    "assistant_id": assistant_id,
                    "document_id": document_id,
                },
                start_to_close_timeout=activity_timeout,
            )

            self._progress = {"current_step": "succeeded", "progress_pct": 100}

            # Update DB record
            await workflow.execute_activity(
                _update_ingestion_db,
                {
                    "ingestion_id": ingestion_id,
                    "state": "succeeded",
                    "current_step": "succeeded",
                    "progress_pct": 100,
                },
                start_to_close_timeout=timedelta(seconds=30),
            )

            return {"status": "succeeded", "chunks_upserted": result.get("count", 0)}

        except Exception as e:
            self._progress = {"current_step": "failed", "progress_pct": 0}

            await workflow.execute_activity(
                _update_ingestion_db,
                {
                    "ingestion_id": ingestion_id,
                    "state": "failed",
                    "current_step": "failed",
                    "error_message": str(e),
                },
                start_to_close_timeout=timedelta(seconds=30),
            )

            raise


@activity.defn(name="update_ingestion_db")
async def _update_ingestion_db(params: dict) -> None:
    """Update the ingestion record in the database."""
    from sqlmodel import Session

    from src.app.storage.assistants_repo import update_ingestion_state
    from src.app.storage.db import engine

    with Session(engine()) as session:
        update_ingestion_state(
            session,
            params["ingestion_id"],
            state=params.get("state"),
            current_step=params.get("current_step"),
            progress_pct=params.get("progress_pct"),
            error_message=params.get("error_message"),
        )
