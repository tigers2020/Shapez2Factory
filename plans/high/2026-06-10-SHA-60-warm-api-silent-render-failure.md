---
linear_issue: SHA-60
title: Staff graph-preview warm API returns ok:true with empty preview_image_url when PNG render fails
priority: High
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fail-closed warm API when PNG render produces no URL

## Source Issue

- Linear: SHA-60
- Status at planning time: Todo
- Priority: High

## Problem

`POST /internal/staff/macro-pattern/graph-preview/warm/` always returns HTTP 200 with `ok: true` after `PlaywrightPngGraphPreviewRenderer.render()`, even when `preview.image_url` is `None`. Deferred PNG warm queues cannot distinguish success from Playwright render failure.

## Scope

Adjust `macro_pattern_staff_api_graph_preview_warm` to fail closed when no valid PNG URL is produced after render.

## Non-goals

- Changing Playwright renderer retry/disable semantics (SHA-17).
- Rewiring recipe graph editor Django endpoints (SHA-56).
- Public `/api/shape-preview/` behavior (SHA-26).

## Implementation Plan

1. Read current view at `django_apps/web/views/staff_shared.py` lines 60–66 and `PlaywrightPngGraphPreviewRenderer.render()` failure path (`image_url=None`).
2. After `preview = renderer.render(preview_scene)`, set `ok = preview.image_url is not None`.
3. When `ok` is false, include stable error detail (e.g. `error_code: "preview_render_failed"`, `error_message` string) in JSON body; keep HTTP 200 with body flag per staff API canon (or document if 502 preferred).
4. Preserve successful path: `ok: true`, `cache_key`, `preview_image_url` unchanged when URL present.
5. Confirm cache_key mismatch path still returns 400 with `ok: false`.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/graph_preview.py` (read-only unless error reason needed)
- `documents/ai/plan_deferred_png_warm_queue.md` (read for client contract)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py`
- typecheck: `mypy django_apps/web`
- tests: `pytest tests/integration/web/test_graph_preview_warm.py -v`
- build: `python manage.py check`
- manual verification: POST warm with Playwright unavailable; confirm `ok: false` and error detail.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Deferred warm queue clients must handle new `ok: false` — confirm against `plan_deferred_png_warm_queue.md`.
