---
linear_issue: SHA-61
title: Space transport catalog import omits IO signatures for 16 merger/splitter tiles
priority: Low
labels:
  - bug
  - solver
  - spec
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Projector regression test for multi-input merge path cell

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: Low

## Problem

`test_layer04_sprite_projector.py` covers straight and turn resolution only via `space_transport_catalog_min.json`. There is no regression guarding merge-topology cells where `_heuristic_tile_id_and_rotation` cannot apply (multi-input masks).

## Scope

Add one focused unit test in `test_layer04_sprite_projector.py` where a path cell has two inputs, requiring catalog `lookup_io` to hit a merger entry. Extend the minimal catalog fixture if needed to include at least one merger IO signature.

## Non-goals

- No projector algorithm changes beyond test coverage.
- No full golden replay suite expansion.
- No lift-tile coverage.

## Implementation Plan

1. Extend `tests/fixtures/asteroid_lab/space_transport_catalog_min.json` with one merger entry (e.g. `SpaceBelt_YMerger`) including `input_mask_eswn` and `output_mask_eswn` matching Mid plan curated R0 values.
2. In `test_layer04_sprite_projector.py`, add `test_y_merger_two_inputs_resolves_via_catalog_lookup` (name flexible):
   - Build a `CommittedRoute` with a junction cell receiving flows from two directions (e.g. path `((0,0), (1,0), (1,1))` with merge at `(1,0)` depending on mask geometry).
   - Call `project_routes_to_tiles` with `transport_kind="space_belt"`.
   - Assert junction coord is present in output and `tile_id` matches the merger fixture entry.
3. Confirm test fails on current main (junction skipped) and passes after Mid plan masks + fixture update.
4. Run `pytest tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py::test_y_merger_two_inputs_resolves_via_catalog_lookup -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py`
- `tests/fixtures/asteroid_lab/space_transport_catalog_min.json`

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py`
- typecheck: n/a (test-only)
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Multi-input path cell test exists and passes after catalog masks land.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Low priority; defer if Mid/High plans already add sufficient projector coverage — avoid duplicate tests.
- Junction path geometry must match the curated merger mask exactly or the test will be flaky.
