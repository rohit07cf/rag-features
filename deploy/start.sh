#!/bin/sh
set -e

# Route to the correct entrypoint based on Railway service name.
# Railway sets RAILWAY_SERVICE_NAME automatically per service.
case "${RAILWAY_SERVICE_NAME:-api}" in
  *streamlit*) exec deploy/start-streamlit.sh ;;
  *worker*)    exec python -m app.workflows.worker ;;
  *)           exec deploy/start-api.sh ;;
esac
