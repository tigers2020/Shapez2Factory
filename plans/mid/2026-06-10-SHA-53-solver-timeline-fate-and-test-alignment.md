---
linear_issue: SHA-53
title: solver_timeline graph modules are not mounted on any page; pytest still asserts production layout
priority: Mid
labels:
  - ui
  - priority:mid
  - refactor
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Decide solver_timeline fate and align tests/docs

## Source Issue

- Linear: SHA-53
- Status at planning time: In Progress
- Priority: Mid

## Problem

Legacy Canvas/DOM recipe-graph UI under `django_apps/web/static/web/js/solver_timeline/` (`graph_mount.js`, `graph_markup.js`, `graph_viewport.js`, `graph_detail.js`, `throughput_summary.js`, `dom_utils.js`) is orphaned: `mountGraph()` and `updateThroughputSummary()` have no callers outside the folder. Public `/solver/` loads only `quick_solver_preview.js` (imports `TIMELINE_DEBOUNCE_MS` from `constants.js`). Staff graph editing uses `frontend/recipe_graph_editor/` → `recipe-graph-editor.js`.

## Scope

Make and document the product/engineering decision: retire/archive legacy `solver_timeline/` graph modules OR wire them to an intended page entrypoint. Align tests and docs to the chosen path. Coordinate with High plan (quarantine false-positive layout tests).

## Non-goals

- Rewriting the React Flow recipe graph editor
- Changing graph-layout bundle CI (SHA-35) or recipe-graph-editor CI (SHA-40)
- Implementing the full public shape solver feature on `/solver/`

## Implementation Plan

1. Confirm product intent: `/solver/` template shows "Under construction"; staff graphs are React Flow only. Default assumption: **retire** legacy Canvas graph UI for public solver redesign window.
2. **If retire (recommended):**
   - Add deprecation header to each `solver_timeline/*.js` graph module (except `constants.js` if kept) or move to `django_apps/web/static/web/js/_archived/solver_timeline/`.
   - Document in `documents/ai/manuals/frontend.md` (or solver redesign note): production graph editing = `recipe-graph-editor.js`; `solver_timeline/` graph modules are not mounted.
   - Ensure High plan quarantine/removal of layout string-contract tests is merged.
   - Leave `quick_solver_preview.js` working; only `constants.js` remains actively imported.
3. **If wire (only if product explicitly requires legacy UI):**
   - Add ES module entry in `solver.html` (or dedicated partial) that imports `mountGraph` from `graph_mount.js`.
   - Restore template markup for `[data-solver-throughput-summary]` and wire `updateThroughputSummary` caller.
   - Add integration test that solver page response includes graph mount script and smoke-checks DOM hooks.
   - Re-enable production layout contract tests (reverse High plan quarantine).
4. Update `.agent-loop/reviewed-areas.md` or issue comment with final fate statement.
5. Cross-check SHA-56 (recipe graph editor Django wiring) — do not duplicate staff editor work; public solver legacy UI is separate concern.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/solver_timeline/*.js`
- `django_apps/web/templates/web/solver.html`
- `django_apps/web/static/web/js/quick_solver_preview.js`
- `documents/ai/manuals/frontend.md`
- `tests/unit/web/test_solver_graph_markup.py` (fate-dependent)
- `tests/integration/web/test_web_smoke.py` (fate-dependent)
- `frontend/recipe_graph_editor/` (reference only, no rewrite)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `powershell -File scripts/test_fast.ps1`
- build: N/A (unless wiring adds new static bundle)
- manual verification: load `/solver/` — confirm no broken script errors; staff recipe graph editor still loads on its staff route (if wired)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] `solver_timeline/` fate documented (wired or retired).
- [ ] Tests/docs updated to match chosen path.

## Risks / Open Questions

- **Product decision required:** retire vs wire. Issue Proposed Approach defers to "Under construction" — default retire unless stakeholder overrides.
- `macro_recipe_graph_visual.py` serializes for `mountGraph` JSON shape; if retired, docstring/comment drift only (no runtime mount).
- Relocating `TIMELINE_DEBOUNCE_MS` is Low plan; do not block Mid on that.
