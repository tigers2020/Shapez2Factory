---
linear_issue: SHA-61
title: Space transport catalog import omits IO signatures for 16 merger/splitter tiles
priority: Low
labels:
  - priority:mid
  - test
  - bug
  - solver
  - spec
status: planned
created_by: todo-plan-automation
---

# Plan: Sprite projector regression for multi-input merge-topology path cell

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: Low

## Problem

`test_space_transport_catalog_import.py` covers Forward + lift only. `sprite_projector._heuristic_tile_id_and_rotation` requires exactly one input and one output direction, so multi-input merge cells are skipped when `catalog.lookup_io` misses. No projector regression guards merge-topology cells after catalog IO fix.

## Scope

Add regression in sprite projector tests where a path cell has two inputs so `catalog.lookup_io` must hit a merger entry and emit a transport tile.

## Non-goals

- L5 A* routing changes.
- Lift-tile IO signatures.
- Full golden replay for all 16 merger/splitter variants.

## Implementation Plan

1. Open `tests/unit/asteroid_lab/test_layer04_sprite_projector.py` (or create if absent).
2. Build minimal route cell with two input directions requiring a merger tile (e.g. `SpaceBelt_TripleMerger` or `SpaceBelt_YSplitter`).
3. Import catalog with Mid plan signatures; call `project_routes_to_tiles`.
4. Assert cell is not skipped and projected `tile_id` matches expected merger entry.
5. Run `pytest tests/unit/asteroid_lab/test_layer04_sprite_projector.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py`
- `tests/unit/asteroid_lab/test_layer04_sprite_projector.py` (new or extended)
- `django_apps/asteroid_lab/services/space_transport_catalog_import.py` (dependency)
- `tests/unit/asteroid_lab/test_space_transport_catalog_import.py` (reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/unit/asteroid_lab/test_layer04_sprite_projector.py -v`
- build: N/A
- manual verification: Test fails before Mid IO signatures; passes after

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Projector regression for multi-input path cell added.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Test fixture must use catalog imported with real game-data masks, not hand-rolled partial catalog, to catch integration gaps.
