"""Application error hierarchy — structured, typed exceptions.

These map to HTTP status codes via FastAPI exception handlers.
"""

from __future__ import annotations


class AppError(Exception):
    """Base for all application errors."""

    def __init__(self, message: str, details: str = ""):
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found (maps to HTTP 404)."""
    pass


class ValidationError(AppError):
    """Input validation failure (maps to HTTP 400/422)."""
    pass


class ExternalServiceError(AppError):
    """Third-party service unavailable or failed (maps to HTTP 502)."""
    pass


class ConfigError(AppError):
    """Required configuration missing or invalid (maps to HTTP 500)."""
    pass
