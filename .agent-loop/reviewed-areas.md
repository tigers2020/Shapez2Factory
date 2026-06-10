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
