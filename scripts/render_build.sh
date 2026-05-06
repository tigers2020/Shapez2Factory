#!/usr/bin/env bash
# Render (or any Linux deploy): frontend bundles + Python deps + migrate + collectstatic.
# Set this as the service Build Command, or: bash scripts/render_build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
npm ci
# Root package.json does not list recipe_graph_editor deps; install before tsc/vite build.
npm --prefix frontend/recipe_graph_editor ci
npm run build
# Server-side graph PNG (Playwright): pin browsers under the repo so the deploy slug can find them.
# Gunicorn still needs `node` on PATH at runtime; many PaaS Python images omit it — then set
# SOLVER_GRAPH_PREVIEW_RENDERER=noop on the web service.
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$PWD/.cache/ms-playwright}"
npx playwright install chromium
poetry install
poetry run python manage.py migrate --noinput
poetry run python manage.py collectstatic --noinput
