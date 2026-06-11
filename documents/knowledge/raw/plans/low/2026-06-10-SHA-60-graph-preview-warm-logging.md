---
linear_issue: SHA-60
title: Graph preview warm — operator logging on render failure
priority: Low
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Log graph preview warm render failures for operators

## Source Issue

- Linear: SHA-60
- Status at planning time: Todo
- Priority: Low

## Problem

When warm endpoint returns `ok: false`, operators lack server-side log context for diagnosing Playwright render failures.

## Scope

Optionally log render failure reason from renderer when `preview.image_url` is missing.

## Non-goals

- Changing renderer disable/retry behavior (SHA-17).

## Implementation Plan

1. After high plan lands, add `logger.warning` in warm view when `preview.image_url is None`.
2. Include `cache_key` and renderer failure hint if available from `GraphPreview` or renderer state.
3. Avoid logging full `preview_scene` payload (size/sensitivity).

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/graph_preview.py` (if exposing last error reason)

## Validation Plan

- manual: trigger failed render; confirm structured log line
- tests: optional caplog assertion in integration test

## Acceptance Criteria

- [ ] Failed warm requests emit operator-visible log entry.
- [ ] No sensitive/large payload in logs.

## Risks / Open Questions

- Renderer may not expose failure reason today; may log generic `render_failed` only.
