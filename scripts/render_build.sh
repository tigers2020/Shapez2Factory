#!/usr/bin/env bash
# Render (or any Linux deploy): frontend bundles + Python deps + static collection.
# Set this as the service Build Command, or: bash scripts/render_build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
npm ci
npm run build
poetry install
poetry run python manage.py collectstatic --noinput
