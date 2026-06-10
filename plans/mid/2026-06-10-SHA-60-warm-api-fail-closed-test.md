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

# Plan: Warm API fail-closed response and render-failure regression test

## Source Issue

- Linear: SHA-60
- Status at planning time: Todo
- Priority: Mid

## Problem

Warm endpoint unconditionally returns `ok: True` after render even when `preview.image_url` is missing.

## Scope

Adjust `macro_pattern_staff_api_graph_preview_warm` to return `ok: false` with stable error detail when no valid PNG URL is produced. Add integration test with mocked renderer failure.

## Non-goals

- SHA-17 renderer disable semantics.
- SHA-56 recipe graph editor wiring.
- SHA-26 public shape-preview API.

## Implementation Plan

1. In `macro_pattern_staff_api_graph_preview_warm`, after `preview = renderer.render(preview_scene)`:
   - If `preview.image_url` is None/empty: return `JsonResponse({"ok": False, "error": "<stable code>", "cache_key": expected_key, "preview_image_url": ""})` (HTTP 200 per issue; or 502 if canon prefers).
   - Else: keep existing success payload unchanged.
2. Add test in `tests/integration/web/test_graph_preview_warm.py`:
   - Mock `PlaywrightPngGraphPreviewRenderer.render` to return `GraphPreview(alt_text="x", image_url=None)`.
   - POST warm endpoint with valid staff auth + payload.
   - Assert `response.json()["ok"] is False` and error field present.
3. Run `pytest tests/integration/web/test_graph_preview_warm.py -v`.
4. Run `python manage.py check`.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `tests/integration/web/test_graph_preview_warm.py`
- `django_apps/web/services/graph_preview.py` (read-only; `GraphPreview` type)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py tests/integration/web/test_graph_preview_warm.py`
- typecheck: `mypy django_apps/web/views/staff_shared.py`
- tests: `pytest tests/integration/web/test_graph_preview_warm.py -v`
- build: `python manage.py check`

## Acceptance Criteria

- [ ] Failed PNG render returns `ok: false` with stable error detail.
- [ ] Successful render path unchanged.
- [ ] Integration test with mocked renderer failure.
- [ ] No change to SHA-17 renderer disable semantics.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.

## Risks / Open Questions

- Stable error code string — pick existing enum/constant if project has staff API error codes; else add documented string.
