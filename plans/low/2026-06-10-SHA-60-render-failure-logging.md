---
linear_issue: SHA-60
title: Staff graph-preview warm API returns ok:true with empty preview_image_url when PNG render fails
priority: Low
labels:
  - bug
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Operator logging for graph-preview warm render failures

## Source Issue

- Linear: SHA-60
- Status at planning time: Todo
- Priority: Low

## Problem

When PNG warm render fails, operators have no server-side log trail tying the warm request to the renderer failure reason.

## Scope

Optionally log render failure reason from renderer when warm endpoint returns `ok: false`.

## Non-goals

- Changing renderer retry/disable behavior (SHA-17).
- Required for acceptance — optional polish.

## Implementation Plan

1. Inspect `PlaywrightPngGraphPreviewRenderer` for existing failure messages or exceptions in `_generate_and_store`.
2. On warm `ok: false` path, `logger.warning` with `cache_key`, staff user id, and renderer failure hint (no secrets).
3. Verify log line appears in dev run with mocked failure.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/graph_preview.py` (read failure surface)

## Validation Plan

- tests: optional; Mid plan test covers contract
- manual verification: trigger mocked failure; confirm log line

## Acceptance Criteria

- [ ] Matches the source issue spec (optional Low item).
- [ ] Stays within the priority scope.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Log volume if warm queue retries aggressively — use warning level once per request.
