---
linear_issue: SHA-49
title: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts
priority: Low
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Pattern Lab multi-layer integration regression

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: Low

## Problem

No integration test covers Pattern Lab HTTP GET with colon-separated multi-layer shape codes. Server contract for multi-layer analysis is unguarded against regression.

## Scope

Add integration test `GET /solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` expecting per-layer output, not a hard error.

## Non-goals

- Full browser E2E coverage.
- Testing every four-layer permutation.

## Implementation Plan

1. Read `tests/integration/web/test_pattern_lab.py` for existing GET patterns.
2. Add test case: `client.get("/solver/pattern-lab/", {"code": "CuCuCuCu:CuCuCuCu"})`.
3. Assert HTTP 200 and response body contains per-layer markers (not `"single-layer shape codes only"`).
4. Assert single-layer existing test still passes unchanged.
5. Run `pytest tests/integration/web/test_pattern_lab.py -v`.

## Files / Areas Likely Affected

- `tests/integration/web/test_pattern_lab.py`

## Validation Plan

- lint: `ruff check tests/integration/web/test_pattern_lab.py`
- tests: `pytest tests/integration/web/test_pattern_lab.py -v`
- build: `python manage.py check`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High/Mid plan landing first; test will fail until analysis and template support multi-layer.
