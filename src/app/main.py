"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.logging import setup_logging
from src.app.storage.db import create_tables


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
