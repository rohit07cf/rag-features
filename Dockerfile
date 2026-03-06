FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy source first (needed for pip install)
COPY pyproject.toml .
COPY src/ src/

# Install Python dependencies (non-editable for production)
RUN pip install --no-cache-dir ".[dev]"

# Copy remaining files (tests, config, docs, etc.)
COPY . .

# Re-copy src/ to guarantee it survives COPY . .
COPY src/ src/

# Verify src/ exists at build time
RUN ls -la /app/src/ && python -c "import sys; sys.path.insert(0,'/app'); import src; print('OK: src package found')"

# Ensure 'src' is importable
ENV PYTHONPATH=/app

# Create data directory and ensure scripts are executable
RUN mkdir -p /app/data && chmod +x /app/deploy/*.sh

EXPOSE 8000 8501
