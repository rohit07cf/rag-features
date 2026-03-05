"""Temporal worker process — registers workflows and activities."""

from __future__ import annotations

import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from app.logging import setup_logging
from app.storage.db import create_tables
from app.workflows.activities.chunk_text import chunk_text
from app.workflows.activities.clean_text import clean_text
from app.workflows.activities.embed_batches import embed_batches
from app.workflows.activities.extract_text import extract_text
from app.workflows.activities.upsert_pinecone import upsert_pinecone
from app.workflows.ingestion_workflow import IngestionWorkflow, _update_ingestion_db


async def main():
    setup_logging()
    create_tables()

    address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "rag-ingestion")

    print(f"Connecting to Temporal at {address}...")
    client = await Client.connect(address)

    print(f"Starting worker on task queue: {task_queue}")
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[IngestionWorkflow],
        activities=[
            extract_text,
            clean_text,
            chunk_text,
            embed_batches,
            upsert_pinecone,
            _update_ingestion_db,
        ],
    )

    print("Worker running. Ctrl+C to stop.")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
