---
linear_issue: SHA-60
title: Staff graph-preview warm API returns ok:true with empty preview_image_url when PNG render fails
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

When PNG generation fails, operators have no server-side log of the failure reason from the warm endpoint.

## Scope

Optionally log render failure reason from renderer when warm endpoint returns `ok: false`.

## Non-goals

- Changing renderer retry/disable behavior (SHA-17).
- Exposing internal exception strings to clients (log only).

## Implementation Plan

1. Inspect `PlaywrightPngGraphPreviewRenderer` for last failure reason or exception message (may need read-only accessor if not exposed).
2. In `macro_pattern_staff_api_graph_preview_warm`, when `preview.image_url is None`, log at WARNING with `cache_key` and failure reason.
3. Do not add failure reason to client JSON unless spec requires it (issue says optional logging only).
4. Add unit test or caplog assertion if logging is straightforward.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/graph_preview.py` (possible small accessor for last error)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py`
- typecheck: `mypy django_apps/web`
- tests: optional caplog in integration test
- build: n/a
- manual verification: Trigger render failure; confirm log line in server output.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Renderer may not retain failure reason today; minimal accessor change must stay within SHA-17 non-goals (no disable-semantics change).
