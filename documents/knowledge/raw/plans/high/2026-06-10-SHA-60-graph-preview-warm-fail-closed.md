---
linear_issue: SHA-60
title: Staff graph-preview warm API silent failure on empty preview_image_url
priority: High
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fail-closed graph preview warm when PNG render returns no URL

## Source Issue

- Linear: SHA-60
- Status at planning time: Todo
- Priority: High

## Problem

`POST /internal/staff/macro-pattern/graph-preview/warm/` always returns HTTP 200 with `ok: true` even when `PlaywrightPngGraphPreviewRenderer.render()` fails and `preview.image_url` is `None`. Clients get `preview_image_url: ""` with no error signal; deferred PNG warm queues cannot detect render failures.

## Scope

Adjust warm endpoint response contract to fail closed when `preview.image_url` is missing after render.

## Non-goals

- Changing Playwright renderer retry/disable semantics (SHA-17).
- Recipe graph Django wiring (SHA-56).
- Public shape preview API (SHA-26).

## Implementation Plan

1. Edit `macro_pattern_staff_api_graph_preview_warm` in `django_apps/web/views/staff_shared.py`.
2. After `preview = renderer.render(preview_scene)`, set `ok = preview.image_url is not None`.
3. When `ok` is false, include stable `error` or `error_code` field (e.g. `render_failed`) in JSON body.
4. Keep HTTP 200 with body `ok: false` (per issue proposed approach) unless project API canon prefers 502/503 — document choice.
5. Preserve success path: `ok: true`, `cache_key`, non-empty `preview_image_url`.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/graph_preview.py` (read only unless logging added in low plan)
- `documents/ai/plan_deferred_png_warm_queue.md` (reference)

## Validation Plan

- tests: mid/low plan integration test
- lint: `ruff check django_apps/web/views/staff_shared.py`
- manual: POST warm with broken Playwright env should return `ok: false`

## Acceptance Criteria

- [ ] Failed PNG render returns `ok: false` with stable error detail.
- [ ] Successful render path unchanged.
- [ ] No change to SHA-17 renderer disable semantics.

## Risks / Open Questions

- HTTP status code vs body-flag-only failure: align with existing staff JSON API patterns.
