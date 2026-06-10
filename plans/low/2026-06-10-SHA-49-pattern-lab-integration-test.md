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

# Plan: Pattern Lab multi-layer integration regression

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: Low

## Problem

No integration regression covers GET `/solver/pattern-lab/` with colon-separated multi-layer codes expecting per-layer output instead of hard error.

## Scope

Add integration test asserting multi-layer Pattern Lab page returns success with per-layer content.

## Non-goals

- Changing service or template beyond test contract

## Implementation Plan

1. Add test case to `tests/integration/web/test_pattern_lab.py`.
2. GET with `code=CuCuCuCu:CuCuCuCu`; assert 200 and per-layer markers in response body.
3. Assert single-layer existing tests still pass.

## Files / Areas Likely Affected

- `tests/integration/web/test_pattern_lab.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/integration/web/test_pattern_lab.py -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High/Mid implementation landing first.
