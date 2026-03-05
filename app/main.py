"""FastAPI application entry point.

This is the heart of the RAG (Retrieval-Augmented Generation) system.

Complete RAG Flow - End to End:
================================

1. DOCUMENT INGESTION (Offline/Batch):
   User uploads PDF → Temporal workflow → Extract text → Chunk → Embed → Store in Pinecone
   Result: Knowledge base of vectorized document chunks

2. USER QUERY PROCESSING (Real-time):
   User asks question → Convert to vector → Search Pinecone → Rerank → Pack context

3. ANSWER GENERATION (Real-time):
   LLM receives: [Retrieved context] + [User question] → Generates cited answer

4. RESPONSE WITH CITATIONS:
   User gets factual answer + source references for verification

Key Components:
- FastAPI: REST API endpoints
- Temporal: Reliable document processing workflows
- Pinecone: Vector database for similarity search
- OpenAI: Embeddings + LLM generation
- Reranking: Cross-encoders for better relevance

Real-Time Example:
User: "What's our return policy?"
1. Query → vector search → finds policy chunks
2. LLM → "Returns accepted within 30 days [Source 1, p.5]"
3. User → clicks citation → sees original policy document

This system transforms static documents into interactive, accurate chat assistants.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.logging import setup_logging
from app.storage.db import create_tables
from app.domain.models.errors import (
    ConfigError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from app.api.routes_assistants import router as assistants_router
from app.api.routes_chat import router as chat_router
from app.api.routes_documents import router as documents_router
from app.api.routes_ingestions import router as ingestions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle.

    Real-time initialization:
    - Setup structured logging for monitoring
    - Create database tables for assistants/documents metadata
    - System ready to accept document uploads and queries
    """
    setup_logging()
    create_tables()
    yield


app = FastAPI(
    title="RAG Assistant Studio API",
    description="Temporal-powered RAG ingestion with multi-provider LLM support",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handlers — map domain errors to HTTP responses ────


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error_code": "NOT_FOUND", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"error_code": "VALIDATION_ERROR", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(ExternalServiceError)
async def external_service_handler(request: Request, exc: ExternalServiceError):
    return JSONResponse(
        status_code=502,
        content={
            "error_code": "EXTERNAL_SERVICE_ERROR",
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(ConfigError)
async def config_error_handler(request: Request, exc: ConfigError):
    return JSONResponse(
        status_code=500,
        content={"error_code": "CONFIG_ERROR", "message": exc.message, "details": exc.details},
    )


# Register routers

app.include_router(assistants_router)
app.include_router(documents_router)
app.include_router(ingestions_router)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "rag-assistant-studio"}
