#!/bin/sh
cd /app
export PYTHONPATH=/app:${PYTHONPATH:-}
exec python -m uvicorn src.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
