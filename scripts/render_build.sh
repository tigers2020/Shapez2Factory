#!/usr/bin/env bash
# Render (or any Linux deploy): frontend bundles + Python deps + migrate + collectstatic.
# Set this as the service Build Command, or: bash scripts/render_build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
npm ci
# Root package.json does not list recipe_graph_editor deps; install before tsc/vite build.
npm --prefix frontend/recipe_graph_editor ci
npm run build
poetry install
poetry run python manage.py migrate --noinput
poetry run python manage.py collectstatic --noinput
