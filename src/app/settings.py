"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the RAG platform."""

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
    log_level: str = "INFO"
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 50

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
