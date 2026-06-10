---
linear_issue: SHA-61
title: Space transport catalog import omits IO signatures for 16 merger/splitter tiles
priority: Mid
labels:
  - bug
  - solver
  - spec
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Curated R0 IO masks and unit test for all routable tiles

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: Mid

## Problem

`_R0_IO_SIGNATURES` maps only Forward/LeftTurn/RightTurn. Unit tests cover Forward + lift only; no merger/splitter assertion.

## Scope

Populate `_R0_IO_SIGNATURES` (or sibling map) for all 16 merger/splitter belt+pipe ids. Add `test_import_routing_allowed_tiles_have_io_signature` asserting 38 routable non-lift tiles have signatures.

## Non-goals

- L5 routing logic changes
- Lift tile signatures

## Implementation Plan

1. Use visual-oracle / game-data workflow noted in import comment for ESWN masks at rotation 0.
2. Extend `_R0_IO_SIGNATURES` for all 16 ids; keep lifts excluded.
3. Add unit test counting 38 routable tiles with `io_signature` (54 total − 16 lifts).
4. Assert `SpaceBelt_TripleMerger` (or similar) resolves via `catalog.lookup_io`.
5. Run `pytest tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- `tests/unit/asteroid_lab/test_space_transport_catalog_import.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] All 38 routable non-lift tiles have `io_signature` after import
- [ ] Representative merger/splitter resolves via `catalog.lookup_io`
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Mask values must match game-data authority; document source in test or comment.
