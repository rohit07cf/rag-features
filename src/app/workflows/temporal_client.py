"""Temporal client helpers for starting and querying workflows."""

from __future__ import annotations

import os

from temporalio.client import Client

from src.app.rag.utils.ids import make_workflow_id

_client: Client | None = None


async def get_client() -> Client:
    """Get or create a Temporal client (singleton)."""
    global _client
    if _client is None:
        address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
        _client = await Client.connect(address)
    return _client


async def start_ingestion_workflow(
    ingestion_id: str,
    document_id: str,
    file_path: str,
    chunk_strategy: str,
    assistant_id: str,
    user_id: str,
) -> str:
    """Start a durable ingestion workflow in Temporal.

    Returns the workflow ID.
    """
    client = await get_client()
    workflow_id = make_workflow_id("ingest")

    from src.app.workflows.ingestion_workflow import IngestionWorkflow

    await client.start_workflow(
        IngestionWorkflow.run,
        {
            "ingestion_id": ingestion_id,
            "document_id": document_id,
            "file_path": file_path,
            "chunk_strategy": chunk_strategy,
            "assistant_id": assistant_id,
            "user_id": user_id,
        },
        id=workflow_id,
        task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "rag-ingestion"),
    )

    return workflow_id


async def query_ingestion_progress(workflow_id: str) -> dict | None:
    """Query a running workflow for its progress state."""
    if not workflow_id:
        return None
    try:
        client = await get_client()
        handle = client.get_workflow_handle(workflow_id)
        result = await handle.query("get_progress")
        return result
    except Exception:
        return None
