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

# Plan: Projector regression for multi-input merger path cell

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: Low

## Problem

No projector test covers a path cell with two inputs requiring merger catalog lookup.

## Scope

Add regression in `test_layer04_sprite_projector.py` (or equivalent) for multi-input path cell.

## Non-goals

- Import implementation (Mid plan).
- L5 routing changes.

## Implementation Plan

1. Build minimal route snapshot with a cell having two input directions (merger topology).
2. Load catalog with merger signatures from Mid plan.
3. Call `project_routes_to_tiles` (or direct projector helper).
4. Assert cell is not skipped and resolves to expected `SpaceBelt_*` / `SpacePipe_*` tile id.
5. Run `pytest tests/unit/asteroid_lab/test_layer04_sprite_projector.py -v` (create file if missing).

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_layer04_sprite_projector.py` (or TBD if test lives elsewhere)
- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py`

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/`
- typecheck: n/a
- tests: `pytest tests/unit/asteroid_lab/test_layer04_sprite_projector.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Exact test file path TBD — confirm with `glob **/test*sprite_projector*`.
