#!/usr/bin/env bash
# Render start: apply migrations (SQLite/ephemeral DB must exist before requests), then gunicorn.
# Set Start Command to: bash scripts/render_start.sh
# Render injects PORT / GUNICORN_CMD_ARGS for binding (see Render Python docs).
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="python3"
fi
"$PYTHON" manage.py migrate --noinput
exec "$PYTHON" -m gunicorn config.wsgi:application
