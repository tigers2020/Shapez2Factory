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

# Plan: Stop sprite projection from dropping merge/split transport cells

## Source Issue

- Linear: SHA-61
- Status at planning time: Todo
- Priority: High

## Problem

L5 sprite projection (`project_routes_to_tiles`) calls `catalog.lookup_io` first. Merger/splitter catalog entries lack `io_signature`, so lookup misses and the single-port heuristic returns `None` for multi-input/multi-output masks. The projector then `continue`s and omits those cells, so merge-aware committed routes render with missing transport tiles in replay/visual output.

## Scope

Verify and close the end-to-end path: imported catalog exposes merger/splitter IO masks → `lookup_io` resolves multi-port signatures → `project_routes_to_tiles` emits `ProjectedTransportTile` rows for merge-topology path cells instead of skipping them.

Depends on Mid plan (`_R0_IO_SIGNATURES` population) completing first.

## Non-goals

- No L5 A* routing or merge-group registry changes.
- No lift-tile IO signatures (`routing_allowed=False` stays).
- No simulation JSON auto-parser for port masks.

## Implementation Plan

1. After Mid plan lands, re-run import against committed `documents/game_data/research_unlocks.json` + `simulation_systems.json`; confirm zero `routing_allowed` entries with `io_signature is None` (expect 38 signed, 16 lifts unsigned).
2. Pick a representative merger mask (e.g. `SpaceBelt_YMerger` R0 ESWN pair from curated map) and assert `SpaceTransportTileCatalog.lookup_io(transport_kind="space_belt", input_mask=..., output_mask=...)` returns that tile id.
3. Build or extend a catalog fixture that includes at least one merger entry (not only `space_transport_catalog_min.json` straight/turn tiles).
4. Construct a `CommittedRoute` whose path has a cell with two input directions (merge junction). Call `project_routes_to_tiles` and assert the junction coord appears in output with a merger `tile_id` (not absent due to `continue`).
5. Run `pytest tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py -v` plus import tests from Mid plan.
6. If golden/replay fixtures exist for merge routes, spot-check one does not lose transport cells post-fix.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py` (read-only verification unless skip logic must change — prefer catalog fix)
- `src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py` (`lookup_io`)
- `django_apps/asteroid_lab/services/space_transport_catalog_import.py` (via Mid plan masks)
- `tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py`
- `tests/fixtures/asteroid_lab/space_transport_catalog_min.json` (may need merger entries for isolated projector tests)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py`
- typecheck: `mypy django_apps config src` (spot-check touched modules)
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_sprite_projector.py tests/unit/asteroid_lab/test_space_transport_catalog_import.py -v`
- build: n/a
- manual verification: Import full catalog; confirm merge-topology path cell resolves to merger tile id in projector output

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Sprite projector no longer skips merge-topology cells due to IO miss.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- High plan is blocked until Mid plan adds curated R0 masks; coordinate execution order.
- Wrong ESWN masks will pass import tests but fail visual/replay golden — visual-oracle provenance for each merger/splitter variant must be documented alongside mask entries.
- `lookup_io` rotation handling: confirm R0 canonical masks align with `canonical_rotation` field on catalog entries.
