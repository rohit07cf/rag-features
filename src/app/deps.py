"""FastAPI dependency injection helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Generator

from sqlmodel import Session

from src.app.settings import Settings, get_settings
from src.app.storage.db import engine


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLModel session, auto-closing on exit."""
    with Session(engine()) as session:
        yield session


@lru_cache
def settings() -> Settings:
    return get_settings()
