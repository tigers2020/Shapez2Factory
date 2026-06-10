---
linear_issue: SHA-60
title: Staff graph-preview warm API returns ok:true with empty preview_image_url when PNG render fails
priority: High
labels:
  - bug
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Fail-closed warm API when PNG render produces no URL

## Source Issue

- Linear: SHA-60
- Status at planning time: In Progress
- Priority: High

## Problem

`POST /internal/staff/macro-pattern/graph-preview/warm/` always returns HTTP 200 with `ok: true` after `PlaywrightPngGraphPreviewRenderer.render()`, even when PNG generation fails and `preview.image_url` is `None`. Clients receive `preview_image_url: ""` with no error signal, so the deferred PNG warm queue cannot distinguish success from a failed Playwright render and silently shows blank graph tiles.

## Scope

Adjust `macro_pattern_staff_api_graph_preview_warm` in `staff_shared.py` to return `ok: false` with a stable error detail when `preview.image_url` is missing after render. Keep HTTP 200 with body flag (consistent with existing staff JSON APIs that use `ok`).

## Non-goals

- Changing Playwright renderer retry/disable semantics (SHA-17).
- Rewiring recipe graph editor Django endpoints (SHA-56).
- Public `/api/shape-preview/` behavior (SHA-26).

## Implementation Plan

1. Open `django_apps/web/views/staff_shared.py` and locate `macro_pattern_staff_api_graph_preview_warm` (lines 48–67).
2. After `preview = renderer.render(preview_scene)`, branch on `preview.image_url is not None`.
3. On success, return unchanged payload: `{"ok": True, "cache_key": expected_key, "preview_image_url": preview.image_url}`.
4. On failure (missing URL), return HTTP 200 with:
   - `"ok": False`
   - `"cache_key": expected_key` (preserve for client correlation)
   - `"preview_image_url": ""`
   - `"error": "render_failed"` (stable string; matches staff API `error` field pattern in `public_pages.py`)
5. Do not change `PlaywrightPngGraphPreviewRenderer.render()` latch behavior.
6. Manually verify deferred warm client in `documents/ai/plan_deferred_png_warm_queue.md` can branch on `ok === false` to retry or surface failure.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `documents/ai/plan_deferred_png_warm_queue.md` (consumer contract reference only; no edit required unless docs drift)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py`
- typecheck: `mypy django_apps config src` (focused on changed module)
- tests: covered by Mid-priority regression test plan
- build: `python manage.py check`
- manual verification: POST warm with scene that forces render failure; confirm `ok: false` and `error: render_failed`

## Acceptance Criteria

- [ ] Failed PNG render returns `ok: false` with stable error detail.
- [ ] Successful render path unchanged.
- [ ] Deferred warm queue can detect render failure from response body.
- [ ] No change to SHA-17 renderer disable semantics.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- HTTP 502/503 was mentioned as alternative in issue spec; current staff APIs prefer HTTP 200 + `ok` flag — confirm no downstream client expects non-2xx on render failure.
- Empty `preview_image_url` on failure is retained for backward compatibility; clients must check `ok` first.
