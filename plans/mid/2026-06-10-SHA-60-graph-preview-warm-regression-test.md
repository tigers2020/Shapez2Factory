---
linear_issue: SHA-60
title: Graph preview warm — mocked render-failure integration test
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Add integration test for graph preview warm render failure

## Source Issue

- Linear: SHA-60
- Status at planning time: Todo
- Priority: Mid

## Problem

`tests/integration/web/test_graph_preview_warm.py` covers auth and cache_key mismatch only; no contract test for render failure returning `ok: false`.

## Scope

Add mocked render-failure integration test asserting `ok: false` and error detail when `PlaywrightPngGraphPreviewRenderer.render` returns `GraphPreview` with `image_url=None`.

## Non-goals

- SHA-17 renderer instance reuse fix.
- Real Playwright integration in CI.

## Implementation Plan

1. Extend `tests/integration/web/test_graph_preview_warm.py`.
2. Mock `PlaywrightPngGraphPreviewRenderer.render` to return `GraphPreview(alt_text="x", image_url=None)`.
3. POST valid `cache_key` + `preview_scene`; assert response `ok is False`, `preview_image_url == ""`, error field present.
4. Add success mock case to ensure regression does not break happy path.

## Files / Areas Likely Affected

- `tests/integration/web/test_graph_preview_warm.py`
- `django_apps/web/views/staff_shared.py` (implementation from high plan)

## Validation Plan

- tests: `pytest tests/integration/web/test_graph_preview_warm.py -v`

## Acceptance Criteria

- [ ] Integration test with mocked renderer failure passes after high plan.
- [ ] Successful render path test still passes.

## Risks / Open Questions

- Mock patch target path must match view import site.
