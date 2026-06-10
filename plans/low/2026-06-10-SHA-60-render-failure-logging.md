---
linear_issue: SHA-60
title: Staff graph-preview warm API returns ok:true with empty preview_image_url
priority: Low
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Operator logging for graph preview render failures

## Source Issue

- Linear: SHA-60
- Status at planning time: Todo
- Priority: Low

## Problem

When PNG generation fails, operators have no server-side log signal beyond empty `preview_image_url` in the response.

## Scope

Optionally log render failure reason from renderer for operators when warm endpoint returns `ok: false`.

## Non-goals

- Changing renderer disable/retry semantics (SHA-17)
- Client-side retry logic

## Implementation Plan

1. After High plan fail-closed branch, log warning with cache_key and failure context.
2. If `GraphPreview` or renderer exposes failure reason, include in log message.
3. Do not leak internal paths in JSON response unless API canon requires it.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/graph_preview.py` (read-only)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py`
- typecheck: `mypy django_apps config src`
- tests: existing warm tests still pass
- build: N/A
- manual verification: Log line appears on mocked failure

## Acceptance Criteria

- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Optional per issue; skip if High/Mid deliver sufficient operator signal.
