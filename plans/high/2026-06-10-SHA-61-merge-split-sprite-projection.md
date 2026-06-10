---
linear_issue: SHA-61
title: Space transport catalog import omits IO signatures for 16 merger/splitter tiles
priority: High
labels:
  - priority:mid
  - bug
  - solver
  - spec
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Fix merge/split transport cell drops in sprite projection

## Source Issue

- Linear: SHA-61
- Status at planning time: In Progress
- Priority: High

## Problem

`project_routes_to_tiles` calls `catalog.lookup_io` first; on miss it falls back to `_heuristic_tile_id_and_rotation`, which requires exactly one input and one output direction. Merger/splitter path cells have multi-port masks, so both lookup and heuristic fail and the cell is skipped (`continue`). Merge-aware committed routes therefore render with missing transport tiles in replay/visual output.

## Scope

Deliver end-to-end behavior where merge/split topology cells project to the correct `SpaceBelt_*` / `SpacePipe_*` tile ids instead of being dropped. Depends on Mid plan completing catalog IO signatures; this plan verifies projector behavior once signatures exist.

## Non-goals

- Changing L5 A* routing logic or merge-group registry behavior.
- Adding lift-tile IO signatures.
- Rewriting catalog import to parse simulation JSON for port masks.

## Implementation Plan

1. Confirm Mid plan IO masks are merged and import produces lookup-able signatures for all 16 merger/splitter ids.
2. Build a minimal committed route fixture where one interior cell has two inputs (e.g. Y-merger: paths from N and S converging at E).
3. Run `project_routes_to_tiles` against imported catalog from `documents/game_data/*.json`.
4. Assert the merge cell is present in output (not skipped) and resolves to expected merger tile id (e.g. `SpaceBelt_YMerger` at R0).
5. Repeat for one splitter topology (one input, two outputs) if merge-only coverage is insufficient.
6. Document any remaining projector gaps (rotation handling, ambiguous mask collisions) in risks.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py`
- `django_apps/asteroid_lab/services/space_transport_catalog_import.py` (consumer of Mid plan)
- `src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py`
- `tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py` (verification; detailed regression may land in Low plan)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/`
- typecheck: `mypy django_apps config src` (spot-check touched modules)
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py -v`
- build: n/a
- manual verification: import catalog against committed game_data; spot-check one merge route projects all path coords

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Sprite projector no longer skips merge-topology cells due to IO miss.
- [ ] Merge/split routes produce complete transport tile lists for replay/visual.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- High outcome is blocked until Mid plan populates `_R0_IO_SIGNATURES` for all 16 merger/splitter ids.
- `lookup_io` rotation expansion must match path-derived masks; wrong R0 curation may still miss at non-zero rotations.
- Sprite `<desc>` tags are the visual-oracle source; filename/desc mismatches on Left/Right Fwd variants need careful cross-check.
