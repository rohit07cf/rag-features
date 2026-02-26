"""Shared test fixtures."""

from __future__ import annotations

import os

import pytest
from sqlmodel import Session, SQLModel, create_engine

# Force test database
os.environ["DATABASE_URL"] = "sqlite:///./test_data/test.db"
os.environ["OPENAI_API_KEY"] = "sk-test-fake"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-fake"
os.environ["PINECONE_API_KEY"] = "test-fake"
os.environ["APP_ENV"] = "test"


@pytest.fixture
def db_session():
    """Provide a clean SQLite session for each test."""
    os.makedirs("test_data", exist_ok=True)
    engine = create_engine("sqlite:///./test_data/test.db", connect_args={"check_same_thread": False})

    from src.app.storage.models import Assistant, IngestionRecord  # noqa: F401

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    # Cleanup
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def sample_text():
    return """# Introduction

This is a sample document for testing chunking strategies.
It contains multiple sections with various content types.

## Methods

We used several approaches to analyze the data.
The primary method was statistical analysis using Python.
Additional validation was performed using cross-validation techniques.

## Results

The results show significant improvement across all metrics.
Accuracy improved by 15% compared to the baseline model.
Precision and recall both exceeded 90% on the test set.

## Discussion

These findings suggest that the proposed approach is effective.
Further research could explore larger datasets and additional models.

## Conclusion

In summary, our approach demonstrates strong performance.
We recommend adoption for production use cases.
"""
