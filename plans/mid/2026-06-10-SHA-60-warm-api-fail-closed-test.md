---
linear_issue: SHA-60
title: Staff graph-preview warm API returns ok:true with empty preview_image_url when PNG render fails
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Warm API fail-closed flag and mocked render-failure test

## Source Issue

- Linear: SHA-60
- Status at planning time: Todo
- Priority: Mid

## Problem

View returns `ok: True` unconditionally; `test_graph_preview_warm.py` covers auth and cache_key mismatch only.

## Scope

Implement `ok: preview.image_url is not None` response contract; add integration test with mocked renderer failure.

## Non-goals

- SHA-17 renderer disable semantics.
- SHA-56 editor wiring.
- SHA-26 public shape-preview API.

## Implementation Plan

1. Update `macro_pattern_staff_api_graph_preview_warm` JsonResponse to set `ok` from `preview.image_url is not None`.
2. Add `error_code` / `error_message` fields when `ok` is false (stable strings for client retry logic).
3. In `test_graph_preview_warm.py`, patch `PlaywrightPngGraphPreviewRenderer.render` to return `GraphPreview(alt_text="x", image_url=None)`.
4. Assert response `ok is False`, non-empty error detail, HTTP 200 (or documented alternate status).
5. Assert existing success-path tests still pass (add mock returning valid URL if Playwright not available in CI).

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `tests/integration/web/test_graph_preview_warm.py`
- `django_apps/web/services/graph_preview.py` (`GraphPreview` dataclass — read-only)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py tests/integration/web/test_graph_preview_warm.py`
- typecheck: `mypy django_apps/web`
- tests: `pytest tests/integration/web/test_graph_preview_warm.py -v`
- build: `python manage.py check`
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Mock strategy must not require Playwright in CI for success-path coverage.
