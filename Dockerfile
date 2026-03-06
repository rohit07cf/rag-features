FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy source first (editable install needs the package to exist)
COPY pyproject.toml .
COPY src/ src/

# Install Python dependencies (non-editable for reliable imports in production)
RUN pip install --no-cache-dir ".[dev]"

# Copy remaining files (tests, config, docs, etc.)
COPY . .

# Ensure 'src' is importable
ENV PYTHONPATH=/app

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8000 8501
