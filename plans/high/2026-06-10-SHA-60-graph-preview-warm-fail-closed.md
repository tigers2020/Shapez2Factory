---
linear_issue: SHA-60
title: Staff graph-preview warm API returns ok:true with empty preview_image_url
priority: High
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fail-closed graph preview warm when PNG render fails

## Source Issue

- Linear: SHA-60
- Status at planning time: Todo
- Priority: High

## Problem

`POST /internal/staff/macro-pattern/graph-preview/warm/` always returns HTTP 200 with `ok: true` even when `PlaywrightPngGraphPreviewRenderer.render()` fails and `preview.image_url` is `None`. Deferred PNG warm queues cannot distinguish success from failed render.

## Scope

Adjust warm endpoint response contract to fail closed when `preview.image_url` is missing after render.

## Non-goals

- Changing Playwright renderer retry/disable semantics (SHA-17)
- Rewiring recipe graph editor Django endpoints (SHA-56)
- Public `/api/shape-preview/` behavior (SHA-26)

## Implementation Plan

1. Read `macro_pattern_staff_api_graph_preview_warm` in `staff_shared.py` (lines 60–66).
2. After `preview = renderer.render(...)`, set `ok` based on `preview.image_url is not None`.
3. Return stable error detail when `ok` is false (message or error code).
4. Preserve successful render response shape unchanged.
5. Verify warm queue client can branch on `ok` flag.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/graph_preview.py` (read-only)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_graph_preview_warm.py -v`
- build: N/A
- manual verification: Mocked failed render returns `ok: false`

## Acceptance Criteria

- [ ] Failed PNG render returns `ok: false` with stable error detail
- [ ] Successful render path unchanged
- [ ] No change to SHA-17 renderer disable semantics
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- HTTP status: issue allows HTTP 200 with body `ok: false` or HTTP 502/503; follow existing staff API canon.
