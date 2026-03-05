"""Application settings loaded from environment variables.

Uses pydantic-settings for typed, validated configuration.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the RAG platform.

    All fields are loaded from environment variables (case-insensitive).
    Required-for-feature fields (pinecone, azure) are validated at point-of-use,
    not at startup, so the app starts without all keys configured.
    """

    # --- LLM providers ---
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # --- Pinecone ---
    pinecone_api_key: str = ""
    pinecone_index_name: str = "rag-assistant"
    pinecone_host: str = ""

    # --- Azure Document Intelligence ---
    azure_docintel_endpoint: str = ""
    azure_docintel_key: str = ""
    azure_docintel_model: str = "prebuilt-layout"

    # --- Temporal ---
    temporal_address: str = "localhost:7233"
    temporal_task_queue: str = "rag-ingestion"
    temporal_namespace: str = "default"

    # --- Database ---
    database_url: str = "sqlite:///./data/assistants.db"

    # --- API ---
    api_base_url: str = "http://localhost:8000"

    # --- App ---
    app_env: str = "local"
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = Field(default=50, ge=1, le=500)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def is_pinecone_configured(self) -> bool:
        return bool(self.pinecone_api_key)

    @property
    def is_azure_docintel_configured(self) -> bool:
        return bool(self.azure_docintel_endpoint and self.azure_docintel_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
