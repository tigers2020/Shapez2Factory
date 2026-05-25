# Capacity C-GATE — Complete-Map Capacity Contract Design

**Date:** 2026-05-28  
**Status:** Proposed for implementation after docs PR merge  
**Track:** v0.1 next-track selection → **capacity C-GATE**  
**Owner:** Asteroid Lab / RTTP capacity and Lab observability  
**Queue authority:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)  
**Depends on:** [`2026-05-26-reconstruction-complete-map-dto-design.md`](2026-05-26-reconstruction-complete-map-dto-design.md), PR #90 tombstones, PR #91 roadmap/current-plan sync

---

## Problem

The repository now correctly tombstones the stale overlay-capacity plan and routes capacity work through `ReconstructionCompleteMap`. However, capacity C-GATE is not yet an executable implementation track until a fresh spec and `current_plan` ACTIVE row exist.

Capacity C-GATE closes that gap. It makes the complete-map capacity contract mechanically enforced across solver runtime, Lab summary, UI observability, and regression gates.

The specific risk to eliminate:

```text
Sparse overlay / ReconstructionResult.cells
  accidentally becomes the terrain capacity or mineable-cell source again.
```

That risk can reappear through helpers, summary code, UI DTOs, tests, or future agents restoring old snippets from tombstoned plans.

---

## North-star contract

```text
cleanup base map + ReconstructionResult overlay
  → build_reconstruction_complete_map(cleanup, recon)
  → ReconstructionCompleteMap
       .cells
       .field_cells
       .shape_field_cell_count
       .fluid_field_cell_count
       .external_void_cells
```

`ReconstructionCompleteMap` is the only accepted source for:

- theoretical field capacity,
- `mineable_cells`,
- `OptimizationInput` terrain field cells,
- Lab capacity card numerator,
- resource-specific field counts,
- capacity C-GATE regression assertions.

`ReconstructionResult.cells` remains overlay-stage output only. It must not be treated as a complete terrain map.

---

## Definitions

### Asteroid field cell

```text
asteroid_field_cell :=
  coord in ReconstructionCompleteMap.cells where
  cell_kind ∈ { asteroid_shape_field, asteroid_fluid_field }
```

Includes:

- decode-original asteroid fields,
- topology/inferred interior fill after reconstruction,
- synthetic reconstructed fields materialized into the complete map.

Excludes:

- belts, pipes, space pipes, and other transport,
- miners and extensions unless the complete map stamps the cell as `asteroid_*_field`,
- external void,
- replay-only full_map rows when not materialized through the complete-map factory.

### Theoretical capacity

```text
capacity_upper_bound_platform_count(resource)
  = count(ReconstructionCompleteMap.field_cells for resource)

max_throughput_per_min(resource)
  = field_count(resource)
    × active MiningExtractionRule.mini_unit_output_per_min
    × 4
```

`×4` is the terrain-capacity per-field throughput factor. It does not change RTTP committed throughput and does not imply every field cell can be route-confirmed simultaneously.

---

## In scope

1. Capacity summary APIs accept `ReconstructionCompleteMap` as the canonical input.
2. `OptimizationInput.mineable_cells` is derived from `ReconstructionCompleteMap.field_cells`.
3. `solver_runtime_entry` builds the complete map once and threads it through capacity and optimization code.
4. Lab summary and UI cards display field-capacity numbers from the same complete-map-derived DTO.
5. Tests and architecture guards prevent reintroducing overlay `recon.cells` as a public capacity SoT.
6. Tombstoned capacity/macro plans remain non-executable references only.

---

## Out of scope

- GA / full evolutionary optimization.
- Macro unpause or macro fixture work.
- Route algorithm changes.
- Incremental commit conflict policy changes.
- Validation repair.
- Replay / NDJSON / solver_summary as algorithm input.
- Changing `actual_committed_output_per_min` semantics.
- Changing `MiningExtractionRule` rates or CANON extraction rule rows.
- UI redesign beyond field-capacity copy and values.

---

## Required API shape

### Complete-map public API

Expected stable public surface:

```python
@dataclass(frozen=True, slots=True)
class ReconstructionCompleteMap:
    cells: tuple[DecodedCellDTO, ...]
    field_cells: frozenset[Coord]
    external_void_cells: frozenset[Coord]
    shape_field_cell_count: int
    fluid_field_cell_count: int
    coord_frame: CoordFrame


def build_reconstruction_complete_map(
    *,
    cleanup: CleanupResult,
    recon: ReconstructionResult,
) -> ReconstructionCompleteMap: ...
```

### Field-cell helper API

Allowed:

```python
asteroid_field_cells_from_complete_map(complete_map)
count_asteroid_field_cells_by_resource(complete_map)
```

Forbidden as public production API:

```python
asteroid_field_cells_from_reconstruction(recon)
count_asteroid_field_cells_by_resource(recon)
```

A private test helper may exist only if named as overlay-diagnostic and guarded from production import paths.

---

## Data flow

```text
run_solver_runtime_for_project
  → decode/copy import
  → cleanup/deconstruct snapshot
  → run_topology_reconstruction(cleanup)
  → build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
  → reconstruction_capacity_summary(complete_map=...)
  → optimization_input_from_reconstruction(cleanup=..., recon=..., complete_map=...)
  → run_rttp_pipeline(...)
  → lab summary / UI DTO
```

Only the complete-map DTO crosses the capacity/optimization boundary for field-cell counts.

---

## Validation gates

### C-GATE-1 — Complete-map parity

- `complete_map.cells` equals the merged display/complete map expected by reconstruction replay and Cell detail.
- `complete_map.field_cells` count matches the full-map field summary.
- Overlay field count is allowed to be smaller, but never used as capacity.

### C-GATE-2 — Capacity summary

- Shape and fluid field counts come from `ReconstructionCompleteMap`.
- A synthetic test with many complete-map fields and few overlay fields must report the complete-map count.
- Transport cells are excluded.

### C-GATE-3 — Optimization input

- `OptimizationInput.mineable_cells == complete_map.field_cells`.
- No `ReconstructionResult.cells` field-count path is used for optimization input.

### C-GATE-4 — Runtime threading

- `solver_runtime_entry` builds the complete map once per run.
- Capacity and optimization receive the same complete-map-derived field set.

### C-GATE-5 — Lab/UI observability

- Lab capacity and footprint cards use complete-map field counts.
- Copy text distinguishes theoretical field capacity from committed route-confirmed throughput.

### C-GATE-6 — Contamination guards

Architecture tests must fail on:

- production imports of tombstoned overlay capacity helpers,
- capacity functions accepting only `ReconstructionResult`,
- replay/full_map ORM reads in solver input code,
- validation code mutating layout or repairing routes.

---

## Test strategy

Narrow gate:

```powershell
python -m pytest tests/unit/asteroid_lab/test_complete_map.py tests/unit/asteroid_lab/test_field_cells.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py tests/unit/asteroid_lab/test_optimization_input_adapter.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v --tb=short
```

Architecture gate:

```powershell
python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v --tb=short
```

Reconstruction standing gate:

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

RTTP standing gate:

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v
```

---

## Acceptance criteria

- [ ] Capacity C-GATE implementation PR has no route/commit/macro/GA behavior change.
- [ ] `ReconstructionCompleteMap` is the only capacity terrain SoT.
- [ ] Overlay `ReconstructionResult.cells` cannot be used as production field-count input without failing tests.
- [ ] `current_plan.md` and roadmap identify capacity C-GATE as a selected active track only after this spec/plan lands.
- [ ] Tombstoned plans remain tombstones.
- [ ] All narrow and architecture gates pass.

---

## Rollback rule

If implementation exposes a route/commit regression, rollback capacity threading first. Do not compensate by weakening final validation, replay contracts, FOT guards, or macro pause constraints.
