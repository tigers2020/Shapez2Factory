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

# Plan: Quarantine false-positive solver_timeline layout contract tests

## Source Issue

- Linear: SHA-53
- Status at planning time: In Progress
- Priority: High

## Problem

Pytest treats `solver_timeline/graph_markup.js` and related modules as live production layout contracts (`tests/unit/web/test_solver_graph_markup.py`, `tests/integration/web/test_web_smoke.py::test_solver_graph_viewport_has_explicit_runtime_layout_styles`), but no Django template or production JS entrypoint loads `graph_mount.js`, `graph_markup.js`, or `throughput_summary.js`. CI passes on layout strings for code that is never mounted, giving false confidence.

## Scope

Remove or explicitly quarantine pytest string-contract tests that assert production layout for unmounted `solver_timeline/` graph modules. Replace with tests that match the chosen fate (retired = no production layout assertions; wired = mount + integration smoke).

## Non-goals

- Rewriting the React Flow recipe graph editor (`recipe-graph-editor.js`)
- Changing `solver_graph_layout.js` / `editor_graph_layout.js` build pipeline (SHA-35)
- Implementing the full public shape solver feature
- Deciding long-term product fate of legacy Canvas UI (covered in Mid plan)

## Implementation Plan

1. Confirm no production mount: grep templates and JS entrypoints for `graph_mount`, `graph_markup`, `mountGraph`, `throughput_summary`.
2. If retiring legacy graph UI (expected while `/solver/` is "Under construction"): delete or move `test_solver_graph_markup.py` and `test_solver_graph_viewport_has_explicit_runtime_layout_styles` to a quarantine module (e.g. `tests/quarantine/solver_timeline/`) with a header comment stating modules are not production-mounted.
3. If quarantining: add `pytest.ini` or marker (`quarantine`) and ensure default CI (`scripts/test_fast.ps1`) does not run quarantined tests unless explicitly opted in.
4. Remove any CI implication that `graph_markup.js` layout strings are enforced production contracts; document in test module or `documents/ai/manuals/frontend.md` that staff graphs use `recipe-graph-editor.js`.
5. Run `powershell -File scripts/test_fast.ps1` and confirm no false-positive layout assertions remain in default gates.

## Files / Areas Likely Affected

- `tests/unit/web/test_solver_graph_markup.py`
- `tests/integration/web/test_web_smoke.py` (`test_solver_graph_viewport_has_explicit_runtime_layout_styles`)
- `pytest.ini` or test markers (if quarantine path chosen)
- `documents/ai/manuals/frontend.md` (brief note on retired vs production graph UI)

## Validation Plan

- lint: `ruff check tests/`
- typecheck: `mypy django_apps config src` (unchanged scope expected)
- tests: `powershell -File scripts/test_fast.ps1`
- build: N/A
- manual verification: grep confirms zero template `<script>` / import references to `graph_mount.js` after test change; CI green without layout string contracts on orphan modules

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] CI no longer asserts unused production layout without explicit quarantine marker.

## Risks / Open Questions

- Quarantined tests may rot if legacy Canvas UI returns; link quarantine header to SHA-53 Mid plan decision.
- `macro_recipe_graph_visual.py` still references `mountGraph` JSON shape in docstring — not a test contract but may confuse readers until Mid plan documents fate.
