# Project Review Memory

Tracks bounded review runs for periodic project review automation. Prevents duplicate Linear issues and re-review of recently covered areas.

## Bootstrap

- Initialized: 2026-06-10 (memory file was missing on branch `cursor/project-review-automation-c8c0`).
- Prior automation runs created Linear issues SHA-7–SHA-39 before this file existed; see Linear Backlog for historical coverage.

## 2026-06-10 10:00

Reviewed area:
- path/module/feature: `frontend/recipe_graph_editor/` CI/build pipeline; `.github/workflows/ci.yml`; root `package.json`; `scripts/test_fast.ps1`; `documents/ai/manuals/testing.md`

Skipped:
- `frontend/graph_layout/` — covered by SHA-35 (open Backlog)
- `django_apps/game_data/browse/` — covered by SHA-39 (reviewed ~09:34 UTC)
- `django_apps/asteroid_lab/` replay cache loaders — covered by SHA-37, SHA-38
- Issues labeled `reviewing` — only archived SHA-16 autotest probe

Findings:
- SHA-40: CI never runs recipe graph editor Vitest or build:recipe-graph-editor; committed bundles can drift

Notes:
- `ci.yml` has no Node/npm steps; Vitest and Vite build are manual-only per manuals. Vite outDir writes committed `django_apps/web/static/web/js/recipe_graph_editor/recipe-graph-editor.{js,css}`. Related but distinct from SHA-35 (graph-layout esbuild bundles).
