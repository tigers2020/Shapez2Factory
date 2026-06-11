---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: Low
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Client regression test for parse-error viewer teardown

## Source Issue

- Linear: SHA-52
- Status at planning time: In Progress
- Priority: Low

## Problem

`tests/integration/web/test_web_smoke.py::test_api_shape_preview_parse_error` covers API contract only. No client regression asserts viewers are cleared on parse-error input.

## Scope

Add focused JS unit test or Playwright check for viewer teardown on `ok: false`.

## Non-goals

- API contract tests (already exist).

## Implementation Plan

1. Choose test path: Playwright (preferred per `.cursor/rules/playwright.mdc` for rendered UI) or JS unit test with DOM harness.
2. Playwright flow: load home/solver page with quick preview panel → enter valid code → wait for `[data-shape-gltf-viewer]` → enter invalid parse-error code → assert viewers host has zero `[data-shape-gltf-viewer]` and `[data-quick-preview-error]` visible.
3. Store artifacts under `output/playwright/` if using browser test.
4. Run targeted test command from project Playwright config.

## Files / Areas Likely Affected

- `tests/integration/web/` or `output/playwright/` (new spec TBD per existing layout)
- `django_apps/web/static/web/js/quick_solver_preview.js` (subject under test)

## Validation Plan

- tests: new regression test green after fix
- manual verification: N/A if Playwright covers flow

## Acceptance Criteria

- [ ] Client regression test added.
- [ ] Test fails on pre-fix behavior (viewers remain).
- [ ] Stays within the priority scope.

## Risks / Open Questions

- WebGL/Three.js init timing in CI may need generous wait; follow existing Playwright patterns in repo.
