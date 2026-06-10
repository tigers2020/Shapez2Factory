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

# Plan: Add curated R0 IO masks for 16 merger/splitter transport tiles

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: Mid

## Problem

`import_space_transport_catalog_from_game_data` populates `_R0_IO_SIGNATURES` for only six straight/turn tiles (Forward, LeftTurn, RightTurn × belt/pipe). The remaining 16 `routing_allowed` merger/splitter variants import without `input_mask_eswn` / `output_mask_eswn`, so `SpaceTransportTileCatalog` entries have `io_signature is None`.

## Scope

Extend `_R0_IO_SIGNATURES` in `space_transport_catalog_import.py` with R0 E/S/W/N masks for all 16 merger/splitter tile ids (8 belt + 8 pipe). Add import unit tests asserting every routable non-lift tile has a signature and representative merger/splitter entries resolve via `catalog.lookup_io`.

## Non-goals

- No lift-tile signatures (16 lift ids remain `routing_allowed=False`, `io_signature=None`).
- No rewrite of import to parse `simulation_systems.json` connector geometry.
- No L5 routing logic changes.

## Implementation Plan

1. Enumerate the 16 target tile ids from `documents/game_data/space_transport_identifiers.md` § Straight, turn, merge/split:
   - `SpaceBelt_LeftFwdMerger`, `SpaceBelt_LeftFwdSplitter`, `SpaceBelt_RightFwdMerger`, `SpaceBelt_RightFwdSplitter`
   - `SpaceBelt_YMerger`, `SpaceBelt_YSplitter`, `SpaceBelt_TripleMerger`, `SpaceBelt_TripleSplitter`
   - Pipe equivalents with `SpacePipe_` prefix.
2. Derive R0 `(input_mask_eswn, output_mask_eswn)` tuples per tile using the visual-oracle workflow referenced in the import module comment (sprite/port inspection under `django_apps/web/static/web/assets/sprites/SpaceBelt/` and `SpacePipe/`). Document mask source in a brief comment per tile group.
3. Add all 16 entries to `_R0_IO_SIGNATURES` (or a clearly named sibling dict merged at import time). Keep existing Forward/LeftTurn/RightTurn entries unchanged.
4. Run import locally; confirm exactly **38** `routing_allowed` entries have `io_signature` and **16** lift entries do not.
5. Add `test_import_routing_allowed_tiles_have_io_signature` in `tests/unit/asteroid_lab/test_space_transport_catalog_import.py`:
   - Import from committed `documents/game_data/*.json`
   - Assert `sum(1 for e in catalog.entries if e.routing_allowed and e.io_signature is None) == 0`
   - Assert `sum(1 for e in catalog.entries if e.routing_allowed) == 38`
6. Add `test_merger_resolves_via_lookup_io` (name flexible): pick one curated merger (e.g. `SpaceBelt_YMerger`) and assert `catalog.lookup_io` returns the expected `tile_id` for its R0 masks.
7. Run `pytest tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- `tests/unit/asteroid_lab/test_space_transport_catalog_import.py`
- `documents/game_data/space_transport_identifiers.md` (reference only; update only if mask table aids maintenance)
- `src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py` (read `lookup_io` contract; no change expected)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/space_transport_catalog_import.py tests/unit/asteroid_lab/test_space_transport_catalog_import.py`
- typecheck: `mypy django_apps config src` (spot-check)
- tests: `pytest tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`
- build: `python manage.py check`
- manual verification: Print missing-signature tile ids after import; expect empty list for routable tiles

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] All 38 routable non-lift tiles have `io_signature` after import.
- [ ] Representative merger/splitter resolves via `catalog.lookup_io`.
- [ ] Lift tiles remain excluded from routing signatures.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- R0 ESWN mask correctness is the main regression risk; wrong masks pass count tests but break projector/replay. Cross-check each variant against sprite connector art before merge.
- Left vs right forward merger/splitter naming (`LeftFwdMerger` vs `RightFwdMerger`) must match game rotation semantics at R0 — consult `space_transport_identifiers.md` and existing Forward/Turn mask conventions (W→E flow at R0).
- Related issues SHA-14 and SHA-54 touch L5 routing but are out of scope; only catalog IO gap is addressed here.
