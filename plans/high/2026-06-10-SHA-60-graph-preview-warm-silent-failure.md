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

# Plan: Fail-closed graph-preview warm when PNG render produces no URL

## Source Issue

- Linear: SHA-60
- Status at planning time: Todo
- Priority: High

## Problem

`POST /internal/staff/macro-pattern/graph-preview/warm/` always returns HTTP 200 with `ok: true` after `PlaywrightPngGraphPreviewRenderer.render()`, even when PNG generation fails and `preview.image_url` is `None`. Clients get `preview_image_url: ""` with no error signal — deferred PNG warm queues cannot detect render failures (silent blank graph tiles).

## Scope

Document and fix the operator-facing impact: warm queue / staff tooling must be able to distinguish success from failed render. High priority is the contract gap; implementation details in Mid plan.

## Non-goals

- Changing Playwright renderer retry/disable semantics (SHA-17).
- Rewiring recipe graph editor Django endpoints (SHA-56).
- Public `/api/shape-preview/` behavior (SHA-26).

## Implementation Plan

1. Confirm current warm response in `django_apps/web/views/staff_shared.py` (`macro_pattern_staff_api_graph_preview_warm`, lines ~60–66).
2. Trace `PlaywrightPngGraphPreviewRenderer.render()` failure path in `django_apps/web/services/graph_preview.py` (returns `GraphPreview` with `image_url=None`).
3. Coordinate with Mid plan: `ok` must reflect `preview.image_url is not None`.
4. Verify deferred PNG warm queue consumer can branch on `ok: false` (read `documents/ai/plan_deferred_png_warm_queue.md`).

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/graph_preview.py`
- `documents/ai/plan_deferred_png_warm_queue.md` (read-only)

## Validation Plan

- tests: Mid plan adds mocked failure test
- manual verification: simulate render failure; warm response must not report success with empty URL

## Acceptance Criteria

- [ ] Failed PNG render does not report `ok: true` with empty `preview_image_url`.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- HTTP status vs body `ok` flag — issue allows HTTP 200 with `ok: false`; align with existing staff JSON patterns.
