---
linear_issue: SHA-52
title: quick_solver_preview leaves stale GLTF viewers when shape-preview API returns ok:false
priority: Low
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Client regression test for parse-error GLTF viewer teardown

## Source Issue

- Linear: SHA-52
- Status at planning time: Todo
- Priority: Low

## Problem

`tests/integration/web/test_web_smoke.py::test_api_shape_preview_parse_error` asserts API contract only. No automated test verifies that `quick_solver_preview.js` clears `[data-quick-preview-viewers]` when the user enters invalid shape code after a successful preview.

## Scope

Add a focused client regression test: valid code → preview mounts → invalid code → viewers host empty and error banner visible. Prefer Playwright (repo already has `playwright` devDependency and integration patterns in `tests/integration/web/test_lab_replay_sprite_canvas.py`). JS unit extraction is acceptable only if a harness already exists for `quick_solver_preview.js` (none found — use Playwright).

## Non-goals

- Full GLTF rendering pixel assertions.
- Changing API contracts.
- Broad home/solver page E2E coverage beyond this teardown path.

## Implementation Plan

1. Review Playwright patterns in `tests/integration/web/test_lab_replay_sprite_canvas.py` (`_playwright_chromium_ready`, skipif guards).
2. Create `tests/integration/web/test_quick_solver_preview_teardown.py` (or extend `test_web_smoke.py` if team prefers colocation — keep test name explicit).
3. Test flow:
   - Start Django live server (pytest-django `live_server` fixture).
   - Launch Chromium via Playwright.
   - Navigate to `/` or `/solver/` (page with `[data-shape-preview-panel]`).
   - Fill `[data-shape-preview-code]` with `SuSuSuSu`; wait for `[data-shape-gltf-viewer]` inside `[data-quick-preview-viewers]`.
   - Clear/replace with `not_a_real_code!!!`; wait for `[data-quick-preview-error]:not(.hidden)` and assert `[data-quick-preview-viewers] [data-shape-gltf-viewer]` count is 0.
4. Mark test `@pytest.mark.skipif(not _playwright_chromium_ready(), ...)` consistent with existing web integration tests.
5. Run `pytest tests/integration/web/test_quick_solver_preview_teardown.py -v` (or `-k quick_solver_preview`).

## Files / Areas Likely Affected

- `tests/integration/web/test_quick_solver_preview_teardown.py` (new)
- `django_apps/web/templates/web/home.html` (selectors reference)
- `django_apps/web/static/web/js/quick_solver_preview.js` (behavior under test)
- `package.json` / Playwright install docs (read-only)

## Validation Plan

- lint: `ruff check tests/integration/web/`
- typecheck: `mypy django_apps config src` (if test imports Django apps)
- tests: `pytest tests/integration/web/test_quick_solver_preview_teardown.py -v`
- build: N/A
- manual verification: Run test locally with `npx playwright install chromium` if skipped in CI

## Acceptance Criteria

- [ ] Client regression test added for parse-error viewer teardown.
- [ ] Test fails on pre-fix code (valid preview remains after invalid input).
- [ ] Test passes after High-priority fix.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- GLTF mount is async; test must wait on DOM selector with sufficient timeout for `mountShapeGltfViewer`.
- CI may skip without Chromium — document skip reason; consider optional job with Playwright browsers installed.
- Debounce (`TIMELINE_DEBOUNCE_MS`) requires `fill` + short wait or `page.wait_for_timeout` after input.
