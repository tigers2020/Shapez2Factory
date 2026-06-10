---
linear_issue: SHA-60
title: Staff graph-preview warm API returns ok:true with empty preview_image_url when PNG render fails
priority: Mid
labels:
  - bug
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Regression test for warm API render failure contract

## Source Issue

- Linear: SHA-60
- Status at planning time: In Progress
- Priority: Mid

## Problem

`tests/integration/web/test_graph_preview_warm.py` covers auth and cache_key mismatch only. There is no test asserting that a failed `PlaywrightPngGraphPreviewRenderer.render()` (returning `GraphPreview` with `image_url=None`) produces `ok: false` with error detail from the warm endpoint.

## Scope

Add integration test with mocked renderer failure. Verify successful render path test still passes (extend or add companion test).

## Non-goals

- Running real Playwright in CI for this test (mock renderer).
- Changing renderer internals (SHA-17).
- Testing PNG byte validation or cache hit paths.

## Implementation Plan

1. Read existing tests in `tests/integration/web/test_graph_preview_warm.py`.
2. Add `test_graph_preview_warm_returns_ok_false_when_render_produces_no_url`:
   - Create staff user and authenticated client (copy pattern from `test_graph_preview_warm_rejects_cache_key_mismatch`).
   - Build valid `preview_scene` via `build_preview_scene("CuCuCuCu")` and matching `cache_key`.
   - Patch `django_apps.web.views.staff_shared.PlaywrightPngGraphPreviewRenderer` (or patch at view import site).
   - Mock instance: `cache_key` returns real key; `render` returns `GraphPreview(alt_text="x", image_url=None)`.
   - POST to warm URL; assert HTTP 200, `body["ok"] is False`, non-empty `body.get("error")`, `body["preview_image_url"] == ""`.
3. Add `test_graph_preview_warm_success_unchanged` (optional if existing coverage insufficient):
   - Mock `render` to return `GraphPreview(alt_text="x", image_url="/media/graph-preview-cache/abc.png")`.
   - Assert `ok is True` and URL echoed.
4. Run: `pytest tests/integration/web/test_graph_preview_warm.py -v`.
5. Run full fast gate if available: `powershell -File scripts/test_fast.ps1` (or pytest subset).

## Files / Areas Likely Affected

- `tests/integration/web/test_graph_preview_warm.py`
- `django_apps/web/views/staff_shared.py` (implementation from High plan; test depends on it)

## Validation Plan

- lint: `ruff check tests/integration/web/test_graph_preview_warm.py`
- tests: `pytest tests/integration/web/test_graph_preview_warm.py -v`
- typecheck: `mypy django_apps config src`
- build: `python manage.py check`
- manual verification: none required (mocked)

## Acceptance Criteria

- [ ] Mocked render-failure integration test exists and passes.
- [ ] Successful render path unchanged and covered.
- [ ] Test does not require Playwright browser.
- [ ] Matches source issue acceptance criteria.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Patch target must match where view instantiates `PlaywrightPngGraphPreviewRenderer()` — use `unittest.mock.patch` on `django_apps.web.views.staff_shared.PlaywrightPngGraphPreviewRenderer`.
- Implement High plan before or in same PR as this test.
