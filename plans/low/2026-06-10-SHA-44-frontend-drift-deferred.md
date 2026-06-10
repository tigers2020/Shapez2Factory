---
linear_issue: SHA-44
title: CI never runs build:css; committed app.css can drift from Tailwind source
priority: Low
labels:
  - automation
  - infra
  - ui
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Deferred frontend drift gates and optional local CSS contract test (SHA-44 Low)

## Source Issue

- Linear: SHA-44
- Status at planning time: In Progress
- Priority: Low

## Problem

Beyond `app.css`, other committed frontend bundles (graph-layout, recipe-graph-editor, locale catalogs) can drift from source without CI enforcement. Existing pytest substring checks in `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` only guard a few lab overlay class names — not a full Tailwind rebuild contract.

## Scope

Track separately; do not implement in SHA-44. Optionally add a repo-level pytest that shells out to `npm run build:css` and asserts a clean diff for faster local feedback (only if duplicating the CI step is desired).

## Non-goals

- Do not implement SHA-35, SHA-40, or SHA-42 gates in this card.
- Do not expand lab overlay styling or token mapping.
- Do not replace CI with pytest-only enforcement.

## Implementation Plan

1. Leave graph-layout drift gate to SHA-35 (`build:graph-layout` + diff on `django_apps/web/static/web/js/solver_graph_layout.js` and `editor_graph_layout.js`).
2. Leave recipe-graph-editor drift gate to SHA-40 (Vitest and/or `build:recipe-graph-editor`).
3. Leave locale catalog drift gate to SHA-42 (`build_locale_ko.py` output vs committed `.po`/`.mo`).
4. If local fast feedback is requested after SHA-44 Mid lands: add an opt-in pytest in `tests/unit/web/` or `tests/integration/web/` that runs `npm run build:css` via `subprocess` and asserts `git diff --quiet django_apps/web/static/web/css/app.css`, skipping when `node`/`npm` unavailable.

## Files / Areas Likely Affected

- SHA-35, SHA-40, SHA-42 issue scopes (separate cards)
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (existing substring guards only)
- Optional: new `tests/unit/web/test_app_css_freshness.py` (if local contract test added later)

## Validation Plan

- tests: optional pytest only if step 4 is implemented
- build: covered by SHA-44 Mid CI gate
- manual verification: confirm related Linear cards remain open and unblocked by SHA-44 merge

## Acceptance Criteria

- [ ] Matches the source issue spec (Low items deferred, not folded into Mid CI work).
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Duplicating `npm run build:css` in pytest slows `test_fast` unless marked `slow` or gated on file changes.
- Substring guards in asteroid lab tests must not be mistaken for full CSS freshness coverage.
