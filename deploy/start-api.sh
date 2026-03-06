#!/bin/sh
set -e
cd /app
export PYTHONPATH=/app:${PYTHONPATH:-}
echo "=== DEBUG: ls /app/src/ ==="
ls /app/src/ || echo "ERROR: /app/src/ missing"
exec python -m uvicorn src.app.main:app --app-dir /app --host 0.0.0.0 --port "${PORT:-8000}"
