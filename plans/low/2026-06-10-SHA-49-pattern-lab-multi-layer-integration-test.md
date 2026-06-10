---
linear_issue: SHA-49
title: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts
priority: Low
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Add Pattern Lab multi-layer integration regression

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: Low

## Problem

Existing tests cover `explain_pattern_family_mismatch` multi-layer unit behavior but not the Pattern Lab HTTP path for colon-separated codes.

## Scope

Add integration test `GET /solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` expecting per-layer output, not a hard error.

## Non-goals

- Exhaustive rotation-variant golden coverage.
- Recipe graph validation integration.

## Implementation Plan

1. Open `tests/integration/web/test_pattern_lab.py` and add case for two-layer code.
2. Assert HTTP 200, no `"single-layer shape codes only"` error string, and per-layer markers in response body.
3. Run `pytest tests/integration/web/test_pattern_lab.py -v`.

## Files / Areas Likely Affected

- `tests/integration/web/test_pattern_lab.py`
- `tests/unit/shapez_solver/test_pattern_lab_service.py` (reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/integration/web/test_pattern_lab.py -v`
- build: N/A
- manual verification: Test fails on current hard-reject behavior

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Integration regression added.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Response assertions should target stable test ids or headings, not full HTML snapshots.
