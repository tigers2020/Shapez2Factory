---
linear_issue: SHA-25
title: test_api_shape_preview_empty_code misnamed; gallery assertions hide missing empty-code API regression
priority: Mid
labels:
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fix shape-preview empty-code integration regression test

## Source Issue

- Linear: SHA-25
- Status at planning time: Todo
- Priority: Mid

## Problem

`test_api_shape_preview_empty_code` tests gallery page, not `/api/shape-preview/` empty/whitespace contract.

## Scope

Replace/rename test to assert HTTP 400, `ok: false`, `"Shape code is empty."` for `code=""` and `code="   "`. Move gallery assertions to separate test.

## Implementation Plan

1. Read `tests/integration/web/test_web_smoke.py` and `preview_service.py`.
2. Rewrite `test_api_shape_preview_empty_code` to GET `/api/shape-preview/` with empty/whitespace codes.
3. Extract gallery markup assertions to `test_gallery_page_renders`.
4. Run `pytest tests/integration/web/test_web_smoke.py -k shape_preview -v`.

## Files / Areas Likely Affected

- `tests/integration/web/test_web_smoke.py`
- `django_apps/shapez_core/services/preview_service.py` (read contract)

## Validation Plan

- tests: `pytest tests/integration/web/test_web_smoke.py -k shape_preview -v`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- HTTP status inconsistency for parse errors tracked in SHA-26 (Low).
