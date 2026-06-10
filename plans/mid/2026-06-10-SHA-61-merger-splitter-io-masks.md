---
linear_issue: SHA-61
title: Space transport catalog import omits IO signatures for 16 merger/splitter tiles
priority: Mid
labels:
  - priority:mid
  - bug
  - solver
  - spec
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Curate R0 IO masks for 16 merger/splitter transport tiles

## Source Issue

- Linear: SHA-61
- Status at planning time: In Progress
- Priority: Mid

## Problem

`import_space_transport_catalog_from_game_data` only attaches R0 `input_mask_eswn` / `output_mask_eswn` for six straight/turn tiles. The other 16 `routing_allowed` merger/splitter variants (belt + pipe) import without `io_signature`, breaking `catalog.lookup_io` for multi-port topology.

## Scope

Populate curated R0 E/S/W/N masks for all 16 merger/splitter tile ids in `space_transport_catalog_import.py` and add unit tests asserting every routable non-lift tile (38 total) has an IO signature after import.

## Non-goals

- Lift tiles (16 ids) remain `routing_allowed=False` without IO signatures.
- Parsing simulation JSON for port masks.
- L5 routing or merge-group registry changes.

## Implementation Plan

1. Use sprite visual-oracle `<desc>` tags under `django_apps/web/static/web/assets/sprites/Space{Belt,Pipe}/` as authoritative R0 port direction source (canonical East-facing).
2. Extend `_R0_IO_SIGNATURES` in `space_transport_catalog_import.py` with 16 entries (8 belt + 8 pipe mirror):

   | tile_id | R0 inputs (ESWN) | R0 outputs (ESWN) |
   | ------- | ---------------- | ----------------- |
   | `*_TripleMerger` | F,T,T,T | T,F,F,F |
   | `*_TripleSplitter` | F,F,T,F | T,T,F,T |
   | `*_YMerger` | F,T,F,T | T,F,F,F |
   | `*_YSplitter` | F,F,T,F | F,T,F,T |
   | `*_LeftFwdMerger` | F,T,T,F | T,F,F,F |
   | `*_RightFwdMerger` | F,T,F,T | T,F,F,F |
   | `*_LeftFwdSplitter` | F,F,T,F | T,T,F,F |
   | `*_RightFwdSplitter` | F,F,T,F | T,F,F,T |

   (Prefix each row with `SpaceBelt_` and `SpacePipe_`.)

3. Cross-check Left/Right Fwd variant sprite desc vs filename (known desc/name swap in some SVG files).
4. Add `test_import_routing_allowed_tiles_have_io_signature`: import from committed `documents/game_data/*.json`; assert exactly 38 `routing_allowed` entries each have non-None `io_signature`; assert 16 lift entries have `routing_allowed=False` and `io_signature is None`.
5. Add representative `catalog.lookup_io` assertions for at least one merger (`SpaceBelt_TripleMerger` or `SpaceBelt_YMerger`) and one splitter (`SpaceBelt_YSplitter`).
6. Run `pytest tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- `tests/unit/asteroid_lab/test_space_transport_catalog_import.py`
- `django_apps/web/static/web/assets/sprites/SpaceBelt/` (oracle reference only)
- `django_apps/web/static/web/assets/sprites/SpacePipe/` (oracle reference only)
- `documents/game_data/space_transport_identifiers.md` (reference)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/space_transport_catalog_import.py tests/unit/asteroid_lab/test_space_transport_catalog_import.py`
- typecheck: `mypy django_apps config src` (spot-check)
- tests: `pytest tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`
- build: n/a
- manual verification: one-off script or REPL import; count `io_signature is None` among `routing_allowed=True` entries → expect 0

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] All 38 routable non-lift tiles have `io_signature` after import.
- [ ] Representative merger/splitter resolves via `catalog.lookup_io`.
- [ ] Lift tiles remain excluded from routing signatures.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Sprite desc filename swaps on `LeftFwd*` / `RightFwd*` variants — verify against game behavior before locking masks.
- `SpacePipe_*` sprites may lack `<desc>` tags in repo; mirror belt masks per `space_transport_identifiers.md` symmetry rule.
- Mask tuple order is E,S,W,N — must match `space_transport_catalog_snapshot.lookup_io` rotation logic.
