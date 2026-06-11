---
linear_issue: SHA-61
title: Space transport catalog import omits IO signatures for 16 merger/splitter tiles
priority: High
labels:
  - bug
  - solver
  - spec
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fix missing transport tiles on merge/split routes in sprite projection

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: High

## Problem

16 merger/splitter `routing_allowed` tiles import without `io_signature`. L5 `project_routes_to_tiles` skips cells on IO lookup miss, so merge-aware routes render with missing transport tiles.

## Scope

Ensure merge/split topology cells resolve via catalog IO lookup instead of being skipped.

## Non-goals

- Changing L5 A* routing or merge-group registry.
- Lift-tile IO signatures.
- Full simulation-JSON port parsing rewrite.

## Implementation Plan

1. Confirm 16 tile ids missing signatures via import against `documents/game_data/*.json`.
2. Trace `sprite_projector.py` skip path on `lookup_io` miss + heuristic failure for multi-port cells.
3. After Mid plan adds signatures, verify projector resolves representative merger cell.
4. Spot-check committed route replay for missing belt/pipe tiles before/after.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py`
- `django_apps/asteroid_lab/services/space_transport_catalog_loader.py` (read-only)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/`
- typecheck: `mypy src`
- tests: `pytest tests/unit/asteroid_lab/test_layer04_sprite_projector.py -v` (if exists)
- build: n/a
- manual verification: Replay with merger topology shows transport tiles.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan delivering correct R0 masks from visual oracle.
