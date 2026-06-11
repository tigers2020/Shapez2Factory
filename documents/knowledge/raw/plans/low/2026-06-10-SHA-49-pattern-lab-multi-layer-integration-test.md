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

No integration test covers GET `/solver/pattern-lab/?code=<multi-layer>` expecting per-layer output instead of hard error page.

## Scope

Add integration regression in `tests/integration/web/test_pattern_lab.py` for colon-separated multi-layer code.

## Non-goals

- Unit tests for service layer (High plan).
- E2E browser tests.

## Implementation Plan

1. Add `test_pattern_lab_page_renders_multi_layer_code` (or similar name).
2. GET `/solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` with Django test client.
3. Assert HTTP 200, response contains per-layer markers (e.g. layer index headings or two signature blocks), and does not contain `"single-layer shape codes only"`.
4. Run `pytest tests/integration/web/test_pattern_lab.py -v`.

## Files / Areas Likely Affected

- `tests/integration/web/test_pattern_lab.py`

## Validation Plan

- lint: `ruff check tests/integration/web/test_pattern_lab.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_pattern_lab.py -v`
- build: N/A
- manual verification: N/A (test is the gate)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Assertion selectors depend on Mid plan template structure; implement after or in same PR as UI changes.
