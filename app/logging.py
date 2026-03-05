"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys

from app.settings import get_settings


def setup_logging() -> None:
    """Configure root logger with structured format."""
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet noisy third-party loggers
    for name in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
