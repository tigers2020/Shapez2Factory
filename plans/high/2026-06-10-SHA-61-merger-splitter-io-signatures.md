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

# Plan: Fix missing transport tiles in merge/split sprite projection

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: High

## Problem

`import_space_transport_catalog_from_game_data` only attaches IO signatures for six straight/turn tiles. Sixteen merger/splitter variants lack `io_signature`, causing `project_routes_to_tiles` to skip multi-port cells. Merge-aware committed routes render with missing transport tiles.

## Scope

Ensure merger/splitter catalog entries expose lookup-able IO signatures so sprite projection no longer skips merge-topology cells.

## Non-goals

- Changing L5 A* routing logic or merge-group registry
- Adding lift-tile IO signatures
- Rewriting entire catalog import to parse simulation JSON

## Implementation Plan

1. Read `space_transport_catalog_import.py` and `_R0_IO_SIGNATURES`.
2. Identify 16 `routing_allowed` merger/splitter tile ids missing signatures.
3. Add curated R0 ESWN masks per issue proposed approach.
4. Re-run import against `documents/game_data/*.json`; verify 38 routable non-lift tiles have signatures.
5. Confirm `catalog.lookup_io` resolves representative merger/splitter.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- `django_apps/asteroid_lab/services/space_transport_catalog_loader.py` (read-only)
- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py` (read-only)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/space_transport_catalog_import.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`
- build: N/A
- manual verification: Import snapshot shows signatures for merger/splitter ids

## Acceptance Criteria

- [ ] Sprite projector no longer skips merge-topology cells due to IO miss
- [ ] Representative merger/splitter resolves via `catalog.lookup_io`
- [ ] Lift tiles remain excluded from routing signatures
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- IO masks require visual-oracle / game-data authority; incorrect masks cause wrong tile rotation.
