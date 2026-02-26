"""Typed enums for domain concepts — eliminates stringly-typed fields."""

from __future__ import annotations

from enum import Enum


class AssistantType(str, Enum):
    MODEL_ONLY = "model_only"
    RAG = "rag"


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ChunkStrategy(str, Enum):
    RECURSIVE = "recursive"
    TOKEN = "token"
    HEADING_AWARE = "heading_aware"
    ADAPTIVE = "adaptive"
    CONTEXTUAL_DOCINTEL = "contextual_docintel"


class IngestionState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class IngestionStep(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    CLEANING = "cleaning"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    UPSERTING = "upserting"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
