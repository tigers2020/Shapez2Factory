# Project Review Memory

Tracks bounded review areas and Linear issues created by periodic project review automation.

## 2026-06-10 02:04

Reviewed area:
- path/module/feature: `django_apps/shapez_solver/services/` — recipe graph validation (`validate_graph_document`, input carrier arity, quantity contract, macro visual serialize path); related unit tests under `tests/unit/shapez_solver/`

Skipped:
- `asteroid_lab/` services (SHA-9–SHA-13, SHA-21–SHA-22 already filed)
- `.github/workflows/` CI gaps (SHA-18–SHA-20 already filed)
- L3–L6 solver layers (SHA-1–SHA-6, SHA-14–SHA-15 already filed)
- Recipe graph editor ↔ Django recompute API wiring (deferred — needs product decision, not a single bug card this run)
- Issues labeled `reviewing` (SHA-16 autotest probe)

Findings:
- SHA-23: Recipe graph validate_graph_document skips input-count check for binary operations
- SHA-24: Recipe graph validate_graph_document accepts non-integer quantity; macro visual truncates via int()

Notes:
- `_validate_operation_inputs` uses `continue` when `len(sorted_edges) < need`; repro: `stacker`/`merge` with one input edge pass validation
- `quantity: 2.9` passes `validate_graph_document`; `_graph_node_doc_to_solver` emits `int(2.9)==2`
- `validate_recipe_graph_context` has quantity type checks but no production callers outside tests

## 2026-06-10 02:30

Reviewed area:
- path/module/feature: `django_apps/shapez_core/` — `/api/health/`, `/api/shape-preview/` (`views.py`, `preview_service.py`, `shape_render_scene.py`); integration tests `tests/integration/web/test_web_smoke.py`, `tests/integration/api/test_health.py`; frontend `quick_solver_preview.js`

Skipped:
- `shapez_solver/` recipe graph (SHA-23–SHA-24 reviewed 02:04)
- `asteroid_lab/` services (SHA-9–SHA-13, SHA-21–SHA-22 already filed)
- `.github/workflows/` CI gaps (SHA-18–SHA-20 already filed)
- L3–L6 solver layers (SHA-1–SHA-6, SHA-14–SHA-15 already filed)
- Graph PNG preview renderer (SHA-17 already filed)
- `basedata_import_service.py` IVVD import (out of bounded scope this run)
- Issues labeled `reviewing` (SHA-16 autotest probe)

Findings:
- SHA-25: test_api_shape_preview_empty_code misnamed; gallery assertions hide missing empty-code API regression
- SHA-26: Shape preview API uses HTTP 400 for empty code but HTTP 200 for parse errors

Notes:
- `test_api_shape_preview_empty_code` GETs `/gallery/` instead of `/api/shape-preview/`; no integration test for empty/whitespace `code` → HTTP 400
- `build_shape_preview_response('')` / `'   '` → 400; parse errors → 200 + `ok: false`; frontend checks `data.ok` only
- Multi-pattern list `[SuSuSuSu, CuCuCuCu]` works in service but has no integration test (not filed — low signal)
