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

# Plan: Regression test for parse-error GLTF viewer teardown

## Source Issue

- Linear: SHA-52
- Status at planning time: In Progress
- Priority: Low

## Problem

`test_api_shape_preview_parse_error` asserts API contract only. No client regression ensures `quick_solver_preview.js` clears `[data-quick-preview-viewers]` when preview fetch returns `ok: false`.

## Scope

Add a focused regression test: valid shape code mounts preview → invalid code clears viewers host and shows error banner. Prefer lightweight approach consistent with repo test patterns.

## Non-goals

- Full Playwright E2E suite expansion unless no lighter option exists.
- Changing API contracts or viewer rendering logic.

## Implementation Plan

1. Survey existing JS test infrastructure under `tests/` (Playwright patterns in `test_lab_replay_sprite_canvas.py`, Django template smoke in `test_web_smoke.py`).
2. **Option A (Playwright):** Add integration test loading home or solver page with `[data-shape-preview-panel]`, fill valid code, wait for `[data-shape-gltf-viewer]`, switch to invalid code, assert viewers host has zero `[data-shape-gltf-viewer]` and `[data-quick-preview-error]` is visible. Skip if Chromium unavailable (match existing `@pytest.mark.skipif` pattern).
3. **Option B (JS unit):** If a DOM test harness exists for static modules, import `runPreview` path via extracted testable surface — only if repo already supports it; do not invent new test framework.
4. Name test clearly, e.g. `test_quick_solver_preview_clears_viewers_on_parse_error`.
5. Run focused pytest and document skip reason when Playwright missing.

## Files / Areas Likely Affected

- `tests/integration/web/test_web_smoke.py` or new `tests/integration/web/test_quick_solver_preview.py`
- `django_apps/web/static/web/js/quick_solver_preview.js` (read-only unless export needed for unit test)
- Home/solver templates with `[data-shape-preview-panel]` (read-only)

## Validation Plan

- lint: `ruff check tests/integration/web/`
- typecheck: N/A
- tests: `pytest tests/integration/web/ -k quick_solver_preview -v` (or chosen path)
- build: N/A
- manual verification: optional cross-check with Playwright screenshot if test is skipped in CI

## Acceptance Criteria

- [ ] Client regression test added for parse-error viewer teardown.
- [ ] Test fails on pre-fix behavior (viewers not cleared) when run against old JS.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Playwright may be optional in CI — use `skipif` like `test_lab_replay_sprite_canvas.py`.
- Flaky timing on debounced preview (`TIMELINE_DEBOUNCE_MS`) — use explicit waits in Playwright.
