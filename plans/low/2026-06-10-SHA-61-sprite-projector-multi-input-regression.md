---
linear_issue: SHA-61
title: L4 sprite projector — multi-input path cell regression
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

# Plan: Projector regression for multi-input merge topology cell

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: Low

## Problem

No projector test covers a path cell with two inputs where catalog lookup must hit a merger entry; heuristic fallback requires exactly one input/output and fails.

## Scope

Add optional regression in `test_layer04_sprite_projector.py` for multi-input path cell.

## Non-goals

- L5 A* routing changes.

## Implementation Plan

1. Build minimal route fixture with merge topology (two inputs into one cell).
2. Use imported catalog with merger IO signatures from high plan.
3. Call `project_routes_to_tiles`; assert transport tile id is merger variant, not skipped.
4. Run `pytest tests/unit/asteroid_lab/test_layer04_sprite_projector.py -v -k merger` (or new test name).

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_layer04_sprite_projector.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py`

## Validation Plan

- tests: targeted pytest above

## Acceptance Criteria

- [ ] Multi-input path cell projects to merger tile via `lookup_io`.
- [ ] Test fails on pre-fix catalog (documents regression value).

## Risks / Open Questions

- Fixture complexity; may reuse existing L4 test helpers if present.
