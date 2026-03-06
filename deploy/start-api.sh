#!/bin/sh
set -e
echo "=== DEBUG: pwd=$(pwd) ==="
echo "=== DEBUG: ls /app/src/ ==="
ls /app/src/ 2>&1 || echo "ERROR: /app/src/ does not exist!"
echo "=== DEBUG: PYTHONPATH=${PYTHONPATH:-unset} ==="
echo "=== DEBUG: checking src import ==="
python -c "import sys; sys.path.insert(0, '/app'); import src; print('src package found at', src.__file__)" 2>&1 || echo "ERROR: cannot import src"
echo "=== Starting uvicorn ==="
cd /app
export PYTHONPATH=/app:${PYTHONPATH:-}
exec python -m uvicorn src.app.main:app --app-dir /app --host 0.0.0.0 --port "${PORT:-8000}"
