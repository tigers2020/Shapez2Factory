---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: Low
labels:
  - ui
  - priority:mid
  - test
  - reviewing
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Preview viewer teardown regression test

## Source Issue

- Linear: SHA-52
- Status at planning time: Todo
- Priority: Low

## Problem

JS unit test or Playwright regression for parse-error viewer teardown.

## Scope

Add a focused client or integration regression asserting GLTF viewers are cleared when `/api/shape-preview/` returns `ok: false`.

## Non-goals

- Changing `/api/shape-preview/` status-code contract (SHA-26).
- Refactoring the full shape GLTF viewer stack.
- Recipe graph editor or Lab replay canvas work.

## Implementation Plan

1. Choose test surface: JS unit test against `quick_solver_preview.js` helpers, or Playwright flow on home/solver quick preview.
2. Scenario: mount viewers with valid shape code → submit invalid parse-error code → assert `[data-quick-preview-viewers]` empty and `[data-quick-preview-error]` visible.
3. Assert no `[data-shape-gltf-viewer]` children remain after `ok: false` response.
4. Keep existing `test_api_shape_preview_parse_error` API contract test unchanged.

## Files / Areas Likely Affected

- `tests/integration/web/test_web_smoke.py` or new Playwright/JS test file
- `django_apps/web/static/web/js/quick_solver_preview.js` (test target only)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/integration/web/test_web_smoke.py -v` (or new Playwright test path once added)
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High/Mid `clearViewerHost` fix landing first.
- Playwright may need dev server; document skip reason if environment blocks browser launch.
