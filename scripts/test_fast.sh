#!/usr/bin/env bash
# Daily TDD — fast unit slice (see documents/ai/manuals/testing.md)
set -euo pipefail
cd "$(dirname "$0")/.."
exec python -m pytest -m "unit and not slow" -n auto --dist loadscope "$@"
