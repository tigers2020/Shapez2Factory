---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: F
pr: 2
related_docs:
  - documents/Algorithm/solver_runtime/phase_g_route_probe.md
  - documents/Algorithm/solver_runtime/00_core_principles.md
---

# Phase F ? Geometry Validation

## Purpose

Check whether projected gene is physically valid within asteroid topology. **Does not modify OptimizationInput.**

## Input

```text
OptimizationInput
ProjectedGenePlacement
```

## Output

```text
GeometryValidationResult
```

## Tasks

Validation scope:

```text
extractor ? rim_cells
extensions ? mineable_cells
occupied_cells ? asteroid_cells
route_probe_start ? occupied_cells
route_probe_start valid in bbox / route domain candidate area
no self-overlap
```

Use only `mineable_cells` / `rim_cells` / `asteroid_cells` sets ? direct cell.kind comparison forbidden ([§0.3](00_core_principles.md)).

### Reject reason (enum)

```text
extractor_not_rim
extension_not_mineable
occupied_outside_asteroid
pattern_overlap_self
output_stub_inside_occupied      # legacy enum member ? semantics = route_probe_start inside occupied
output_stub_invalid_coord        # legacy enum member ? semantics = route_probe_start invalid coord
```

**New test function names:** [`00_core_principles.md`](00_core_principles.md) §0.7 ? `test_geometry_rejects_route_probe_start_*` only.

## Forbidden

- placement/route repair in validation
- `OptimizationInput` mutation
- Determining mineable via kind string

## Completion criteria

- [ ] valid/invalid cases return deterministic reject reason
- [ ] geometry stage runs before route probe
- [ ] input DTO unchanged

## Prerequisite phase

```text
test_geometry_accepts_valid_projected_gene
test_geometry_rejects_extractor_not_rim
test_geometry_rejects_extension_not_mineable
test_geometry_rejects_occupied_outside_asteroid
test_geometry_rejects_route_probe_start_inside_occupied
test_geometry_rejects_route_probe_start_invalid_coord
test_geometry_does_not_mutate_optimization_input
```

## Related code?documents

- Implementation: `django_apps/asteroid_lab/optimization/candidate_geometry.py`
- `tests/unit/asteroid_lab/test_candidate_geometry.py` (implementation)

## Next Phase

? [`phase_g_route_probe.md`](phase_g_route_probe.md)
