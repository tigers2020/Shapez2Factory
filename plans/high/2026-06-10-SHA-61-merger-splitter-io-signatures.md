---
linear_issue: SHA-61
title: Space transport catalog missing IO signatures for merger/splitter tiles
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

# Plan: Restore IO signatures so merge/split routes project transport tiles

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: High

## Problem

`import_space_transport_catalog_from_game_data` only attaches R0 IO masks for six straight/turn tiles. Sixteen merger/splitter `routing_allowed` tiles import without `io_signature`. L5 `project_routes_to_tiles` skips cells on IO miss, so merge-aware routes render with missing transport tiles.

## Scope

Ensure merge/split topology cells resolve via `catalog.lookup_io` instead of being skipped in sprite projection.

## Non-goals

- L5 A* routing logic changes.
- Lift-tile IO signatures.
- Full simulation JSON port-mask parser rewrite.

## Implementation Plan

1. Reproduce: import catalog from committed `documents/game_data/*.json`; confirm 16 `routing_allowed` entries with `io_signature is None`.
2. Use visual-oracle / game-data workflow (per import comment) to capture ESWN masks for each merger/splitter at rotation 0.
3. Populate `_R0_IO_SIGNATURES` (or sibling map) for all 16 belt+pipe merger/splitter tile ids.
4. Re-run import; verify `catalog.lookup_io` resolves representative merger (e.g. `SpaceBelt_TripleMerger`) and splitter (e.g. `SpaceBelt_YSplitter`).
5. Smoke-test `project_routes_to_tiles` on multi-input path cell — cell no longer skipped.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- `django_apps/asteroid_lab/services/space_transport_catalog_loader.py`
- `django_apps/asteroid_lab/services/space_transport_catalog_snapshot.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py`
- `documents/game_data/*.json` (reference)

## Validation Plan

- tests: mid/low plan unit tests
- lint: `ruff check django_apps/asteroid_lab/services/space_transport_catalog_import.py`

## Acceptance Criteria

- [ ] Sprite projector no longer skips merge-topology cells due to IO miss.
- [ ] Representative merger/splitter resolves via `catalog.lookup_io`.
- [ ] Lift tiles remain excluded.

## Risks / Open Questions

- IO masks must match game visual oracle; wrong masks cause wrong tile rotation in replay.
