---
linear_issue: SHA-26
title: Shape preview API uses HTTP 400 for empty code but HTTP 200 for parse errors
priority: Low
labels:
  - bug
  - priority:low
status: planned
created_by: todo-plan-automation
---

# Plan: Resolve shape-preview HTTP status contract inconsistency

## Source Issue

- Linear: SHA-26
- Status at planning time: Todo
- Priority: Low

## Problem

Empty code → HTTP 400; parse errors → HTTP 200 + `ok: false`. API consumers cannot rely on status alone.

## Scope

Decide contract (A: always 200+`ok` flag, or B: 400 for all client errors); update service, tests, and `quick_solver_preview.js`.

## Non-goals

- Do not break frontend without updating JS error handling.

## Implementation Plan

1. Decide contract with issue options A vs B (default: B for consistency with empty-code 400 unless frontend prefers A).
2. Update `build_shape_preview_response` in `preview_service.py`.
3. Update integration tests (coordinate with SHA-25).
4. Verify `quick_solver_preview.js` handles chosen contract.
5. Document contract in API docstring or manual.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/preview_service.py`
- `django_apps/web/static/web/js/quick_solver_preview.js`
- `tests/integration/web/test_web_smoke.py`

## Validation Plan

- tests: integration shape_preview tests
- manual verification: preview UI error surfacing

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Contract decision required** before implementation — mark uncertainty here per automation rules (single mid plan would also work; issue label is priority:low so one low plan).
