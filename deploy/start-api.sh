#!/bin/sh
set -e
export PYTHONPATH=/app:${PYTHONPATH:-}
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
