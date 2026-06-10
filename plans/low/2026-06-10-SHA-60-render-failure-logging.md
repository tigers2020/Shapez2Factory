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

# Plan: Operator logging when warm API PNG render fails

## Source Issue

- Linear: SHA-60
- Status at planning time: In Progress
- Priority: Low

## Problem

When `PlaywrightPngGraphPreviewRenderer.render()` fails and returns no `image_url`, operators have no server-side log entry tying the failure to `cache_key` or scene identity. Debugging silent blank tiles requires reproducing the warm request manually.

## Scope

Add structured warning log in `macro_pattern_staff_api_graph_preview_warm` when render completes without `image_url`. Include `cache_key` and a short reason if available from renderer.

## Non-goals

- Exposing internal exception strings to API clients.
- Changing renderer disable latch (SHA-17).
- Adding metrics or alerting infrastructure.

## Implementation Plan

1. Import `logging` in `staff_shared.py` if not present; get module logger.
2. In the render-failure branch (after High plan fail-closed logic), emit:
   - `logger.warning("graph_preview_warm_render_failed cache_key=%s", expected_key)`
3. Optionally inspect `graph_preview.py` `_generate_and_store` for last exception — only log if renderer already exposes failure reason without API contract change; otherwise skip exception detail in v1.
4. Add unit test or extend integration test to assert log record via `caplog` fixture (optional; low priority).
5. Run `ruff check` on changed file.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/graph_preview.py` (read-only unless safe failure reason accessor exists)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py`
- tests: optional `caplog` assertion; not blocking if omitted
- typecheck: `mypy django_apps config src`
- build: `python manage.py check`
- manual verification: trigger failed warm; confirm warning in Django logs

## Acceptance Criteria

- [ ] Failed warm render produces operator-visible log line with `cache_key`.
- [ ] No sensitive data or stack traces returned in JSON response.
- [ ] Stays within Low priority scope.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Renderer may not expose last failure reason without SHA-17 scope creep — log `cache_key` only if reason unavailable.
- Log volume under bulk warm queue; warning level is appropriate.
