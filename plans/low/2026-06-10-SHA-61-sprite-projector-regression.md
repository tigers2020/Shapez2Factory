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

# Plan: Sprite projector regression for multi-input path cell

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: Low

## Problem

No projector test covers a path cell with two inputs where catalog lookup must hit a merger entry. Heuristic fallback requires exactly one input/output and fails for merge topology.

## Scope

Add optional regression in `test_layer04_sprite_projector.py` for a multi-input path cell that requires merger catalog lookup.

## Non-goals

- L5 routing algorithm changes
- Full golden replay suite

## Implementation Plan

1. Read `sprite_projector.py` (`_heuristic_tile_id_and_rotation`, `lookup_io` path).
2. Build minimal route cell fixture with two input directions.
3. Assert projector selects merger tile id (not skip/`continue`).
4. Run `pytest tests/unit/asteroid_lab/test_layer04_sprite_projector.py -v` (or equivalent path).

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_layer04_sprite_projector.py` (or create if absent)
- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py` (read-only)

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/`
- typecheck: `mypy django_apps config src`
- tests: focused projector pytest
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Sprite projector no longer skips merge-topology cells due to IO miss
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Optional per issue; depends on Mid plan IO masks being correct.
