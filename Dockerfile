FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files for install
COPY pyproject.toml .
COPY src/ src/

# Install Python dependencies and verify src is importable from site-packages
RUN pip install --no-cache-dir ".[dev]" \
    && python -c "import src; print('src installed to site-packages OK')"

# Copy remaining files (tests, config, deploy scripts, etc.)
COPY . .

# Ensure 'src' is importable (site-packages from pip install, /app as fallback)
ENV PYTHONPATH=/app

# Create data directory and ensure scripts are executable
RUN mkdir -p /app/data && (chmod +x /app/deploy/*.sh 2>/dev/null || true)

EXPOSE 8000 8501
