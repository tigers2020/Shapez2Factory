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

# Plan: Add R0 IO masks for 16 merger/splitter transport tiles

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: Mid

## Problem

`import_space_transport_catalog_from_game_data` only populates `_R0_IO_SIGNATURES` for six straight/turn tiles; 16 merger/splitter belt+pipe variants have `io_signature is None`.

## Scope

Add curated R0 ESWN masks for all 16 merger/splitter ids; extend unit tests asserting routable non-lift tiles have signatures.

## Non-goals

- L5 routing logic changes.
- Lift tile signatures.
- Simulation JSON auto-parse for ports.

## Implementation Plan

1. Use visual-oracle / game-data workflow (per import comment) to capture R0 `input_mask_eswn` / `output_mask_eswn` for each merger/splitter id (belt + pipe).
2. Extend `_R0_IO_SIGNATURES` (or sibling map) in `space_transport_catalog_import.py`.
3. Run import; verify 38 routable non-lift tiles (54 total − 16 lifts) have `io_signature`.
4. Add `test_import_routing_allowed_tiles_have_io_signature` counting signatures.
5. Add test that representative merger (e.g. `SpaceBelt_TripleMerger`) resolves via `catalog.lookup_io`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- `django_apps/asteroid_lab/services/space_transport_catalog_snapshot.py`
- `tests/unit/asteroid_lab/test_space_transport_catalog_import.py`
- `documents/game_data/*.json` (read-only reference)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- typecheck: `mypy django_apps/asteroid_lab`
- tests: `pytest tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Incorrect oracle masks will pass import tests but fail golden projector tests; validate at least one multi-input projector case (Low plan).
