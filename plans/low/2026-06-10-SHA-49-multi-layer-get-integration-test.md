---
linear_issue: SHA-49
title: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:low
status: planned
created_by: todo-plan-automation
---

# Plan: Integration test GET multi-layer Pattern Lab code

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: Low

## Problem

No integration regression covers Pattern Lab HTTP GET with colon-separated multi-layer codes. Service unit tests cover `explain_pattern_family_mismatch` multi-layer path, but `tests/integration/web/test_pattern_lab.py` does not assert per-layer HTML output for `CuCuCuCu:CuCuCuCu`.

## Scope

Add integration test `GET /solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` expecting per-layer output (not hard error string `"Pattern Lab currently supports single-layer shape codes only."`).

## Non-goals

- Restoring `PatternCatalogRepository`.
- Full four-layer matrix of integration cases.
- Changing single-layer integration assertions beyond ensuring no regression.

## Implementation Plan

1. Open `tests/integration/web/test_pattern_lab.py` and review existing GET patterns and staff/auth fixtures.
2. Add test case: `GET /solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` with expected HTTP 200.
3. Assert response body does not contain single-layer-only error string.
4. Assert per-layer markers present (e.g. layer headings, signature blocks — match template structure from Mid scope).
5. Add negative guard: codes with >4 layers still error per contract.
6. Run: `pytest tests/integration/web/test_pattern_lab.py -v`.

## Files / Areas Likely Affected

- `tests/integration/web/test_pattern_lab.py`
- `django_apps/web/views/public_pages.py` (`pattern_lab` — reference)
- `django_apps/web/templates/` — `pattern_lab.html` (template structure reference)
- `tests/unit/shapez_solver/test_pattern_lab_service.py` (service contract reference)

## Validation Plan

- lint: `ruff check tests/integration/web/test_pattern_lab.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_pattern_lab.py -v`
- build: `python manage.py check`
- manual verification: N/A

## Acceptance Criteria

- [ ] Integration test covers multi-layer GET without hard rejection.
- [ ] Test fails on pre-fix behavior (single-layer-only error).
- [ ] Single-layer integration tests still pass.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.

## Risks / Open Questions

- Template markup choices affect assertion stability — prefer semantic markers over brittle full HTML snapshots.
- Depends on Mid scope template structure for meaningful per-layer assertions.
