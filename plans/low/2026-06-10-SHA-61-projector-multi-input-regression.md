---
linear_issue: SHA-61
title: Space transport catalog import omits IO signatures for 16 merger/splitter tiles
priority: Low
labels:
  - priority:mid
  - bug
  - solver
  - spec
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Sprite projector regression for multi-input path cells

## Source Issue

- Linear: SHA-61
- Status at planning time: In Progress
- Priority: Low

## Problem

`test_layer04_sprite_projector.py` only covers single-input/single-output straight and turn paths. Multi-input merger cells are the failure mode for SHA-61 but have no dedicated projector regression.

## Scope

Add one projector unit test where a path cell has two inputs (merge topology), requiring `catalog.lookup_io` to hit a merger catalog entry rather than the single-port heuristic.

## Non-goals

- Exhaustive rotation coverage for all 16 merger/splitter variants.
- Changing projector implementation beyond what High/Mid plans require.
- Updating `space_transport_catalog_min.json` unless necessary for test isolation.

## Implementation Plan

1. After Mid plan lands, extend `tests/fixtures/asteroid_lab/space_transport_catalog_min.json` with at least one merger entry (e.g. `SpaceBelt_YMerger` with R0 masks) OR import full catalog in test via `import_space_transport_catalog_from_game_data` (prefer fixture if min.json stays small).
2. Add `test_y_merger_two_inputs_resolves_catalog_entry`:
   - Route path where cell `(1,0)` receives from `(1,-1)` (N) and `(0,0)` (W), exits to `(2,0)` (E).
   - Call `project_routes_to_tiles` with `transport_kind="space_belt"`.
   - Assert merge cell `(1,0)` is in output with `tile_id == "SpaceBelt_YMerger"` (or appropriate merger for mask).
   - Assert `len(tiles)` equals expected path length (no skipped cells).
3. Optionally add splitter case (one input, two outputs) in same test file.
4. Run `pytest tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py`
- `tests/fixtures/asteroid_lab/space_transport_catalog_min.json` (if extended)
- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py` (read-only unless High plan finds gaps)

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py`
- typecheck: n/a (test-only)
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Multi-input path cell test exists and passes with full catalog signatures.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan IO masks; test will fail until signatures exist.
- Min fixture vs full game_data import tradeoff: fixture keeps test fast but must stay in sync with import contract.
- Multi-route merge cells (two `CommittedRoute` sharing a coord) may need separate coverage later — out of scope unless repro requires it.
