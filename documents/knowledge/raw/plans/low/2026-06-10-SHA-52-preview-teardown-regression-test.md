---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Add client regression for parse-error viewer teardown (SHA-52 Low)

## Source Issue

- Linear: SHA-52
- Status at planning time: In Progress
- Priority: Low

## Problem

`tests/integration/web/test_web_smoke.py::test_api_shape_preview_parse_error` covers API contract only. No automated check asserts the client clears `[data-quick-preview-viewers]` when parse errors occur.

## Scope

Add a focused client or integration regression that asserts viewers are cleared on parse-error input after a successful preview.

## Non-goals

- Full Playwright suite expansion beyond this one flow unless `/playwright` skill recommends it.
- Changing SHA-26 HTTP status semantics.

## Implementation Plan

1. Prefer a Playwright test under `tests/integration/web/` or `output/playwright/` pattern: load home/solver page with quick preview panel, stub or use known invalid code, assert `[data-quick-preview-viewers]` has no `[data-shape-gltf-viewer]` and `[data-quick-preview-error]` is visible.
2. Alternative: extract `clearViewerHost` / `runPreview` error branch into a small testable module and add a JS unit test if the repo has a Vitest/Jest harness for static JS (check existing patterns first).
3. Run `pytest tests/integration/web/ -k preview -v` or the new Playwright gate per project convention.

## Files / Areas Likely Affected

- `tests/integration/web/test_web_smoke.py` or new `tests/integration/web/test_quick_solver_preview.py`
- `django_apps/web/static/web/js/quick_solver_preview.js`
- Optional Playwright artifacts under `output/playwright/`

## Validation Plan

- tests: new regression test green after Mid plan fix
- manual verification: duplicate High plan browser repro once as sanity check

## Acceptance Criteria

- [ ] Client regression test added for parse-error viewer teardown.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- GLTF mount is async; test must wait for viewers before submitting invalid code.
- Headless WebGL may be flaky in CI — prefer DOM child-count assertions over pixel checks.
