"""Database engine and table creation."""

from __future__ import annotations

import os
from functools import lru_cache

from sqlmodel import SQLModel, create_engine as _create_engine


@lru_cache
def engine():
    url = os.getenv("DATABASE_URL", "sqlite:///./data/assistants.db")
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return _create_engine(url, echo=False, connect_args=connect_args)


def create_tables() -> None:
    """Create all SQLModel tables (idempotent)."""
    from src.app.storage.models import Assistant, IngestionRecord  # noqa: F401

    os.makedirs("data", exist_ok=True)
    SQLModel.metadata.create_all(engine())
