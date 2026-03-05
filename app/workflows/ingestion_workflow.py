"""Temporal workflow for durable document ingestion.

This workflow transforms raw documents into searchable RAG knowledge:

Document Processing Pipeline:
1. Extract: Pull text from PDFs, Word docs, etc.
2. Clean: Remove formatting artifacts, normalize text
3. Chunk: Split into meaningful segments (sentences, paragraphs, sections)
4. Embed: Convert text chunks to vector representations
5. Store: Save vectors in Pinecone for fast similarity search

Why chunking? LLMs have context limits, so we split documents into
bite-sized pieces that fit in the context window while preserving meaning.

Why embeddings? Convert human language to numbers so computers can
measure similarity between questions and document content.

Pipeline: extract -> clean -> chunk -> embed batches -> upsert Pinecone
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import activity, workflow

with workflow.unsafe.imports_passed_through():
    from app.workflows.activities.chunk_text import chunk_text
    from app.workflows.activities.clean_text import clean_text
    from app.workflows.activities.embed_batches import embed_batches
    from app.workflows.activities.extract_text import extract_text
    from app.workflows.activities.upsert_pinecone import upsert_pinecone


@workflow.defn
class IngestionWorkflow:
    """Durable ingestion: extract → clean → chunk → embed → upsert.

    Real-Time Document Processing:
    1. User uploads "company_handbook.pdf"
    2. Extract text from PDF pages
    3. Clean formatting (remove headers, footers, tables)
    4. Split into semantic chunks (paragraphs, sections)
    5. Convert each chunk to vector embedding
    6. Store vectors in database for future retrieval
    7. Later: "What's our vacation policy?" → finds relevant chunks

    Uses Temporal for reliability - if server crashes during embedding,
    workflow resumes from last completed step.
    """

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
            # Step 1: Extract Text from Document
            # Convert PDF/Word/etc. to plain text
            # Example: PDF pages → continuous text stream
            self._progress = {"current_step": "extracting", "progress_pct": 10}
            raw_text = await workflow.execute_activity(
                extract_text,
                {"file_path": file_path, "document_id": document_id},
                start_to_close_timeout=activity_timeout,
            )

            # Step 2: Clean Extracted Text
            # Remove artifacts from PDF conversion (headers, footers, tables)
            # Normalize whitespace, fix encoding issues
            self._progress = {"current_step": "cleaning", "progress_pct": 25}
            cleaned_text = await workflow.execute_activity(
                clean_text,
                {"text": raw_text, "document_id": document_id},
                start_to_close_timeout=activity_timeout,
            )

            # Step 3: Chunk Text into Segments
            # Split long document into smaller, meaningful pieces
            # Strategy examples: by paragraphs, sentences, or semantic sections
            # Each chunk ~200-500 words for optimal retrieval
            self._progress = {"current_step": "chunking", "progress_pct": 40}
            chunks = await workflow.execute_activity(
                chunk_text,
                {
                    "text": cleaned_text,
                    "document_id": document_id,
                    "strategy": chunk_strategy,  # "recursive", "heading_aware", etc.
                    "file_path": file_path,
                },
                start_to_close_timeout=activity_timeout,
            )

            # Step 4: Convert Chunks to Vector Embeddings
            # Transform text into numerical vectors (arrays of numbers)
            # Example: "Solar power is renewable" → [0.1, -0.3, 0.8, ...]
            # Enables mathematical similarity comparison
            self._progress = {"current_step": "embedding", "progress_pct": 60}
            embedded_chunks = await workflow.execute_activity(
                embed_batches,
                {"chunks": chunks, "document_id": document_id},
                start_to_close_timeout=activity_timeout,
            )

            # Step 5: Store Vectors in Database
            # Save embeddings to Pinecone vector database
            # Organized by assistant_id for multi-tenant isolation
            # Enables fast similarity search during RAG queries
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

    from app.storage.assistants_repo import update_ingestion_state
    from app.storage.db import engine

    with Session(engine()) as session:
        update_ingestion_state(
            session,
            params["ingestion_id"],
            state=params.get("state"),
            current_step=params.get("current_step"),
            progress_pct=params.get("progress_pct"),
            error_message=params.get("error_message"),
        )
