"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.app.logging import setup_logging
from src.app.storage.db import create_tables
from src.domain.models.errors import (
    AppError,
    ConfigError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
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
        content={"error_code": "EXTERNAL_SERVICE_ERROR", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(ConfigError)
async def config_error_handler(request: Request, exc: ConfigError):
    return JSONResponse(
        status_code=500,
        content={"error_code": "CONFIG_ERROR", "message": exc.message, "details": exc.details},
    )


# Register routers
from src.app.api.routes_assistants import router as assistants_router
from src.app.api.routes_chat import router as chat_router
from src.app.api.routes_documents import router as documents_router
from src.app.api.routes_ingestions import router as ingestions_router

app.include_router(assistants_router)
app.include_router(documents_router)
app.include_router(ingestions_router)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "rag-assistant-studio"}
