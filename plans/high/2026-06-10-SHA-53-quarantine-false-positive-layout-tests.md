---
linear_issue: SHA-53
title: solver_timeline graph modules are not mounted on any page; pytest still asserts production layout
priority: High
labels:
  - ui
  - priority:mid
  - refactor
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Quarantine false-positive solver_timeline layout CI contracts

## Source Issue

- Linear: SHA-53
- Status at planning time: Todo
- Priority: High

## Problem

Pytest treats `solver_timeline/` Canvas/DOM graph markup strings as live production contracts even though no Django template or JS entrypoint mounts `mountGraph()` or loads `graph_mount.js`, `graph_markup.js`, or `throughput_summary.js`. CI passes on layout details for dead code while staff graph editing uses `recipe-graph-editor.js` (React Flow).

Affected tests:

- `tests/unit/web/test_solver_graph_markup.py` — subprocess probe of `graph_markup.js` layout strings
- `tests/integration/web/test_web_smoke.py::test_solver_graph_viewport_has_explicit_runtime_layout_styles` — static file string assertions on `graph_mount.js`, `graph_markup.js`, `graph_viewport.js`

## Scope

Remove or explicitly quarantine pytest string-contract tests that assert production layout for unmounted `solver_timeline/` modules. Replace with one of:

1. **Retire path (recommended while `/solver/` is "Under construction"):** delete or `@pytest.mark.quarantine` the false-positive tests; add a short comment/doc noting staff graphs are covered by `recipe-graph-editor` CI (SHA-40).
2. **Wire path (only if product chooses legacy Canvas UI):** defer this High plan until Mid plan confirms wiring; then tests remain but must assert mounted runtime behavior, not raw file strings.

This High plan executes immediately once the Mid product decision is recorded (default: retire/defer legacy Canvas UI).

## Non-goals

- Rewriting React Flow `recipe-graph-editor`
- Changing `solver_graph_layout.js` / `editor_graph_layout.js` build pipeline (SHA-35)
- Implementing full public shape solver feature
- Moving `TIMELINE_DEBOUNCE_MS` (Low plan, SHA-53)

## Implementation Plan

1. Confirm Mid plan decision is **retire/defer** (expected given `solver.html` "Under construction" copy).
2. Inventory all tests referencing `solver_timeline/`:
   - `pytest --collect-only -q tests/unit/web/test_solver_graph_markup.py tests/integration/web/test_web_smoke.py`
   - `rg 'solver_timeline|graph_markup|graph_mount|graph_viewport' tests/`
3. **Retire path — unit tests:**
   - Remove `tests/unit/web/test_solver_graph_markup.py` OR move to `tests/quarantine/web/test_solver_graph_markup.py` with explicit `@pytest.mark.quarantine(reason="solver_timeline not mounted; SHA-53")` and ensure quarantine marker is excluded from default CI (match existing quarantine convention if present).
4. **Retire path — integration smoke:**
   - Delete `test_solver_graph_viewport_has_explicit_runtime_layout_styles` from `tests/integration/web/test_web_smoke.py`.
5. Add a one-line regression guard: optional test that documents `mountGraph` has zero production importers (grep-based or import-graph check) — only if team wants a positive "still orphaned" signal instead of silent deletion.
6. Run targeted pytest to confirm no false-positive green on unmounted layout:
   - `pytest tests/unit/web/ tests/integration/web/test_web_smoke.py -v`
7. Run full fast gate: `powershell -File scripts/test_fast.ps1` (or `pytest` equivalent on Linux).

## Files / Areas Likely Affected

- `tests/unit/web/test_solver_graph_markup.py` (delete or quarantine)
- `tests/integration/web/test_web_smoke.py` (remove `test_solver_graph_viewport_has_explicit_runtime_layout_styles`)
- `tests/conftest.py` or pytest config (only if quarantine marker wiring needed)
- `documents/ai/manuals/frontend.md` or solver_timeline README (cross-link to Mid plan doc, optional)

## Validation Plan

- lint: `ruff check tests/unit/web/ tests/integration/web/test_web_smoke.py`
- typecheck: N/A (test-only change)
- tests: `pytest tests/unit/web/ tests/integration/web/test_web_smoke.py -v`
- build: N/A
- manual verification: `rg 'graph_mount|mountGraph' django_apps/web/templates django_apps/web/static/web/js --glob '!solver_timeline/**'` confirms zero production mounts (pre-existing state)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] CI no longer asserts unused production layout without explicit quarantine marker and reason.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- If Mid plan chooses **wire** instead of retire, this High plan must be superseded — tests should shift to browser/DOM integration, not deleted.
- Quarantine vs delete: prefer delete if no near-term re-mount intent; quarantine only if revival is planned within one sprint.
- `macro_recipe_graph_visual.py` still serializes for `mountGraph` JSON shape — unrelated to pytest layout strings but may need doc note if modules archived.
