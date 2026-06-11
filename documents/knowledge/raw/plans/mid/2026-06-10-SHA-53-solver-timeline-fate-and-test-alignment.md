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
- Status at planning time: Todo
- Priority: Mid

## Problem

Legacy Canvas/DOM recipe-graph UI under `django_apps/web/static/web/js/solver_timeline/` is orphaned: `mountGraph()` and `updateThroughputSummary()` have no production callers; only `TIMELINE_DEBOUNCE_MS` from `constants.js` is imported (by `quick_solver_preview.js`). Staff graph editing uses `frontend/recipe_graph_editor/` → `recipe-graph-editor.js`. The public solver page (`solver.html`) is "Under construction" and loads only `quick_solver_preview.js`.

Modules in scope: `graph_mount.js`, `graph_markup.js`, `graph_viewport.js`, `graph_detail.js`, `throughput_summary.js`, `dom_utils.js`, `constants.js`.

## Scope

Record and execute the product decision for `solver_timeline/` graph UI:

### Recommended path (defer legacy Canvas UI)

Given `/solver/` under construction and zero production mounts:

1. Mark `solver_timeline/` graph modules as **deprecated/retired** (README + file-header comments).
2. Do **not** wire `mountGraph()` to any page in this issue.
3. Execute High plan: quarantine/remove false-positive pytest layout contracts.
4. Document that staff recipe graphs use React Flow editor only; link SHA-40 for editor CI.

### Alternate path (revive legacy Canvas UI)

Only if product explicitly requires Canvas graph on a page:

1. Add ES module entry in `solver.html` (or dedicated partial) that imports `mountGraph` from `graph_mount.js`.
2. Restore `[data-solver-throughput-summary]` markup in template and wire `updateThroughputSummary()` caller.
3. Pass graph JSON from an existing API or placeholder stub consistent with `macro_recipe_graph_visual.py` serializer.
4. Replace string-contract pytest with mounted DOM/browser tests (`/playwright` or Playwright pytest).
5. Keep modules active; skip deprecation headers.

Either path must leave tests/docs consistent with reality.

## Non-goals

- Rewriting React Flow recipe graph editor
- Changing `solver_graph_layout.js` / `editor_graph_layout.js` build pipeline (SHA-35)
- Implementing full public shape solver backend/feature
- Relocating `TIMELINE_DEBOUNCE_MS` (Low plan)

## Implementation Plan

1. **Decision checkpoint (required first step):**
   - Read `django_apps/web/templates/web/solver.html` hero copy ("Under construction").
   - Confirm with issue author or default to **retire/defer** when no objection.
   - Record decision in `django_apps/web/static/web/js/solver_timeline/README.md` (create if missing).

2. **Retire/defer path (default):**
   - Add `README.md` under `solver_timeline/` stating: modules not mounted; staff graphs use `recipe-graph-editor.js`; public solver TBD.
   - Add `@deprecated` or banner comment to `graph_mount.js`, `graph_markup.js`, `graph_viewport.js`, `graph_detail.js`, `throughput_summary.js`.
   - Leave `constants.js` in place until Low plan relocates `TIMELINE_DEBOUNCE_MS`.
   - Trigger High plan test quarantine/removal.

3. **Wire path (if chosen):**
   - Create `solver_timeline_entry.js` (or extend `quick_solver_preview.js`) exporting init that calls `mountGraph(panel, graph, options)`.
   - Add `<script type="module">` in `solver.html` with mount target DOM (`data-solver-graph-panel` or equivalent).
   - Add throughput summary container `[data-solver-throughput-summary]` to template.
   - Wire graph data source (document which API endpoint or inline bootstrap JSON).
   - Rewrite tests per wire path (see High plan alternate).

4. **Docs alignment:**
   - Update `documents/ai/manuals/frontend.md` (or nearest web UI doc) with solver_timeline fate one paragraph.
   - Cross-reference related issues SHA-35, SHA-40 in README.

5. **Verification grep (both paths):**
   - `rg 'mountGraph|graph_mount|throughput_summary' django_apps/web/templates django_apps/web/static/web/js --glob '!solver_timeline/**'`
   - Retire path: expect zero matches. Wire path: expect template entry import.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/solver_timeline/` (all graph modules + new README)
- `django_apps/web/templates/web/solver.html`
- `django_apps/web/templates/web/home.html` (verify no latent script tags)
- `django_apps/web/static/web/js/quick_solver_preview.js` (read-only unless wire path)
- `django_apps/shapez_solver/services/macro_recipe_graph_visual.py` (read serializer contract)
- `frontend/recipe_graph_editor/` (read-only reference)
- `documents/ai/manuals/frontend.md`
- `tests/unit/web/test_solver_graph_markup.py` (via High plan)
- `tests/integration/web/test_web_smoke.py` (via High plan)

## Validation Plan

- lint: `ruff check .` (if Python touched); JS unchanged in retire path
- typecheck: `mypy django_apps config src` (if Python touched)
- tests: `pytest tests/unit/web/ tests/integration/web/test_web_smoke.py -v` after High plan
- build: N/A for retire path; `npm run build:recipe-graph-editor` only if wire path touches editor (non-goal)
- manual verification:
  - Retire: load `/solver/` — preview panel works, no graph mount errors in console
  - Wire: load `/solver/` — graph panel renders, throughput summary updates

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] `solver_timeline/` fate documented (wired or retired).
- [ ] Tests/docs updated to match chosen path.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Open:** Explicit product sign-off on retire vs wire — default retire is reasonable but should be noted in PR.
- `macro_recipe_graph_visual.py` still targets `mountGraph` JSON shape; if modules retired, consider follow-up issue to align serializer naming/docs.
- `[data-solver-throughput-summary]` exists only in `throughput_summary.js` today — wire path must add template markup.
- SHA-35/SHA-40 track different bundles; do not conflate solver_timeline Canvas UI with graph-layout npm bundles.
