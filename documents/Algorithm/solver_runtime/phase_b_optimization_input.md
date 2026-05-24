---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: B
pr: 1B
related_docs:
  - documents/Algorithm/solver_runtime/00_core_principles.md
  - documents/Algorithm/asteroid_lab_01_optimization_input.md
---

# Phase B ? Build OptimizationInput

## Purpose

Convert reconstruction snapshot to optimization layer canonical DTO. §0.3 extension kind ? field kind normalization runs at **this adapter boundary**.

## Input

```text
LoadedReconstructionSnapshot
```

## Output

```python
OptimizationInput(
    asteroid_cells=...,
    mineable_cells=...,
    rim_cells=...,
    interior_cells=...,
    external_void_cells=...,
    route_goals=...,              # seed only ? see below
    existing_transport_cells=...,
    existing_trunk_cells=...,
    protected_corridor_cells=...,
    blocked_cells=...,
    topology_graph=...,
    asteroid_bbox=...,
    route_domain_bbox=...,
    bbox=...,  # deprecated alias == route_domain_bbox
)
```

### Dual bbox (Phase B adapter)

| Field | Meaning |
|-------|---------|
| `asteroid_bbox` | Tight inclusive bbox over `mineable_cells` (fallback: all decoded server coords if empty) |
| `route_domain_bbox` | `expand_bbox(asteroid_bbox, OUTER_VOID_PADDING)` with `OUTER_VOID_PADDING = 10` |
| `bbox` | Legacy alias; must equal `route_domain_bbox` |

`external_void_cells` = all coords in `route_domain_bbox` that are **not** occupied decoded cells (`all_sv`). Reconstruction topology compare bbox stays tight (see `topology_contract`); only optimization routing expands.

### `route_goals` boundary (Phase B vs C)

| Phase | `route_goals` role |
|-------|-------------------|
| **B** | **seed / basic only** ? outer void `frozenset()`, minimal goals extracted from existing trunk?transport. **No planned set generation responsibility.** |
| **C** | **planned `RouteGoal` canonical** ? generated?augmented by capacity planner?external margin/void selection. PR2 probe?PR3+ use **post-C** goal set. |

Phase B completion criteria do **not** require external margin goals to be "filled in".

## Tasks

1. Extractor / miner / extension removal coords ? asteroid evidence ? `asteroid_cells` + `mineable_cells`
2. `asteroid_shape_field` / `asteroid_fluid_field` ? both become mineable asteroid field
3. Belt / pipe removal coords ? outside asteroid evidence ? `existing_transport_cells` or route domain evidence
4. `shapeMinerExtension` / `fluidMinerExtension` ? field kind normalization ([`00_core_principles.md`](00_core_principles.md) §0.3)
5. Fix all coords to Server X/Y
6. Split `asteroid_bbox` / `route_domain_bbox` and generate padded `external_void_cells` (`reconstruction_adapter`)

## Forbidden

- Determining mineable via cell.kind in optimizer?candidate_geometry?route_probe interior
- raw?server conversion in optimization interior
- DB original modification

## Completion criteria

- [ ] all coords are Server X/Y
- [ ] mineable field kind does not depend on strict fluid kind in optimizer
- [ ] extension/miner evidence is represented as mineable asteroid field sets
- [ ] `RouteDomainSnapshotBuilder` single entry point can seed `route_domain`
- [ ] `route_goals` is empty or seed only; planned goals are Phase C responsibility

## Prerequisite phase

PR1B ? `tests/unit/asteroid_lab/test_optimization_input.py` (DTO?adapter?coordinates) ? see [`implementation_sequence.md`](implementation_sequence.md).

## Related code?documents

- [`asteroid_lab_01_optimization_input.md`](../asteroid_lab_01_optimization_input.md)
- `django_apps/asteroid_lab/optimization/` ? `OptimizationInput` DTO
- **PR1B partial complete:** `reconstruction_adapter.optimization_input_from_reconstruction`, `route_domain.py` ([`implementation_sequence.md`](implementation_sequence.md))
- **Package canonical:** `asteroid_lab/optimization` only ? `shapez_asteroid` removed ([`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) §2)

## Next Phase

? [`phase_c_capacity_route_goals.md`](phase_c_capacity_route_goals.md)
