---
linear_issue: SHA-61
title: Space transport catalog import omits IO signatures for 16 merger/splitter tiles
priority: High
labels:
  - priority:mid
  - test
  - bug
  - solver
  - spec
status: planned
created_by: todo-plan-automation
---

# Plan: Fix merge/split route projection dropping transport cells

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: High

## Problem

`import_space_transport_catalog_from_game_data` only attaches R0 E/S/W/N `input_mask_eswn` / `output_mask_eswn` for six straight/turn tiles. The other 16 `routing_allowed` merger/splitter variants import without `io_signature`. L5 `project_routes_to_tiles` calls `catalog.lookup_io` first; on miss it falls back to single-input/single-output heuristic. Multi-port merger/splitter masks miss both paths and the cell is skipped, so merge-aware committed routes render with missing transport tiles.

## Scope

Ensure merge/split topology cells project to correct `SpaceBelt_*` / `SpacePipe_*` tile ids instead of being skipped.

## Non-goals

- Changing L5 A* routing logic or merge-group registry behavior.
- Adding lift-tile IO signatures (lifts remain `routing_allowed=False`).
- Rewriting entire catalog import to parse simulation JSON for port masks.

## Implementation Plan

1. Reproduce: import against committed `documents/game_data/*.json`; confirm 16 `routing_allowed` entries with `io_signature is None` (e.g. `SpaceBelt_TripleMerger`, `SpaceBelt_YSplitter`).
2. Add curated R0 IO masks for 16 merger/splitter belt+pipe tile ids in import module.
3. Verify `catalog.lookup_io` resolves representative merger/splitter at rotation 0.
4. Run `project_routes_to_tiles` on multi-input path cell; confirm cell is no longer skipped.
5. Confirm lift tiles remain excluded from routing signatures.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- `django_apps/asteroid_lab/services/space_transport_catalog_loader.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py`
- `django_apps/asteroid_lab/services/space_transport_catalog_snapshot.py` (reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`
- build: N/A
- manual verification: Multi-input merge path renders transport tile in sprite projection output

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Merge/split routes no longer drop transport cells in projection.
- [ ] Representative merger/splitter resolves via `catalog.lookup_io`.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- R0 masks require visual-oracle or game-data authority; incorrect masks cause wrong tile selection at runtime.
