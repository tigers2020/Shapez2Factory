---
linear_issue: SHA-61
title: Space transport catalog import omits IO signatures for 16 merger/splitter tiles
priority: Mid
labels:
  - priority:mid
  - test
  - bug
  - solver
  - spec
status: planned
created_by: todo-plan-automation
---

# Plan: Curated R0 IO masks for 16 merger/splitter tiles plus signature unit test

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: Mid

## Problem

`_R0_IO_SIGNATURES` in `space_transport_catalog_import.py` maps only Forward/LeftTurn/RightTurn (belt + pipe). Inline comment says "Extend via visual oracle before golden Turn/Merger tests." Import yields 16 `routing_allowed` entries without `io_signature`. Unit tests cover Forward + lift only.

## Scope

Populate R0 IO masks for all 16 merger/splitter belt+pipe tile ids and add unit test asserting every routable non-lift tile has `io_signature`.

## Non-goals

- L5 routing logic changes.
- Lift-tile signatures.
- Full simulation JSON port-mask parser.

## Implementation Plan

1. Use visual-oracle / game-data workflow noted in import comment to capture ESWN masks for each merger/splitter at rotation 0.
2. Extend `_R0_IO_SIGNATURES` (or sibling map) for all 16 ids; keep lift tiles excluded.
3. Run `import_space_transport_catalog_from_game_data` against committed game data; verify 38 routable non-lift tiles (54 total − 16 lifts) have signatures.
4. Add `test_import_routing_allowed_tiles_have_io_signature` counting routable tiles with non-null `io_signature`.
5. Add representative merger/splitter `catalog.lookup_io` resolution assertion.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- `tests/unit/asteroid_lab/test_space_transport_catalog_import.py`
- `documents/game_data/*.json` (reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`
- build: N/A
- manual verification: Import log or test output shows zero routable non-lift tiles missing signatures

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] All 38 routable non-lift tiles have `io_signature` after import.
- [ ] Unit test asserts signature coverage.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Mask accuracy depends on visual-oracle source; wrong ESWN bits cause silent wrong-tile projection.
