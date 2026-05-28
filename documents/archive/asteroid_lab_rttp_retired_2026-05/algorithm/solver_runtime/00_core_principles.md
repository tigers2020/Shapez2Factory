---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: ??
pr: ??PR
related_docs:
  - documents/Algorithm/solver_runtime/README.md
  - documents/Algorithm/asteroid_lab_00_overview.md
  - .cursor/rules/asteroid-lab-invariants.mdc
---

# Core Principles (§0)

These apply to all Solver Runtime Phases.

## 0.1 Do not install actual equipment during search

**Forbidden:**

```text
server x/y coordinates used to install actual extractor / extension / belt / pipe
```

**Allowed:**

```text
server x/y coordinates used for deterministic candidate enumeration
```

Coordinate order is **candidate generation order**, not **commit order**.

**Allowed after CONFIRMED:** [`phase_k2_placement_materialization.md`](phase_k2_placement_materialization.md) ? commit-success placement + route reservation is materialized into `MaterializedLayoutCells` (replay·validation output). Immediate install during enumeration·probe stages is forbidden.

## 0.2 Do not install actual target belt/pipe in outer void first?

**Forbidden:**

```text
install belt/pipe in void first and connect everything afterward
```

**Allowed:**

```text
create RouteGoals from external void / margin / existing trunk
```

Actual transport materialization happens in the **post-commit** route network materialization phase. ([`phase_k_route_materialization.md`](phase_k_route_materialization.md))

## 0.3 Reconstruction map loads extension kind as field after normalization

The DB reconstruction map preserves miner extension kinds as raw kinds. The first Solver runtime normalization is converting optimization to **field kind**:

```text
shapeMinerExtension / Layout_ShapeMinerExtension
? asteroid_shape_field

fluidMinerExtension / Layout_FluidMinerExtension
? asteroid_fluid_field
```

- Normalization **does not modify the DB original.**
- Boundary: performed only in the `LoadedReconstructionSnapshot ? OptimizationInput` **adapter**.

The optimizer uses the following sets as canonical after normalization:

```text
OptimizationInput.asteroid_cells
OptimizationInput.mineable_cells
OptimizationInput.rim_cells
OptimizationInput.external_void_cells
OptimizationInput.route_goals
OptimizationInput.route_domain
```

Rules:

```text
asteroid_shape_field ? asteroid_cells + mineable_cells
asteroid_fluid_field ? asteroid_cells + mineable_cells
```

Extension raw kinds are **preserved** for resource/evidence purposes.

**Forbidden (optimizer interior):**

```python
# Direct kind comparison forbidden in candidate_geometry / route_probe interior
cell.kind == "shapeMinerExtension"
cell.kind == "fluidMinerExtension"
cell.kind == "asteroid_fluid_field"
cell.kind == "asteroid_shape_field"
```

Kind assignment is adapter 1st-normalization responsibility; optimizer interior uses only `asteroid_cells` / `mineable_cells` sets.

## 0.4 All candidates must pass route probe to enter normal pool

```text
projected gene
? geometry validation
? route probe
? reachable=True only normal_candidates
```

Unreachable candidates go only to diagnostic / rejected candidate pools.

## 0.5 Candidate phase reachable ? commit success

At commit time, reprobe with the **latest route domain**.

```text
candidate probe success ? final commit success
```

Details: [`phase_j_incremental_commit.md`](phase_j_incremental_commit.md).

## 0.6 Coordinate terms (Runtime canonical, alias forbidden)

| Name | Meaning |
|------|---------|
| `fixed_output_transport` | **First belt/pipe cell** immediately after extractor output (canonical E offset `(1,0)`) |
| `route_probe_start` | Route search **start** cell (offset `(2,0)`; **must not be in occupied_offsets**) |
| `output_stub` | **Legacy** ? **forbidden** in new DTO·function·document field names |

`CandidateRejectReason.output_stub_*` enum member names are **legacy compatibility**; semantics map to `route_probe_start`.

## 0.7 New test·document naming (reject / geometry)

| Scope | Rule |
|------|------|
| **New pytest function names** | `route_probe_start_*` · `fixed_output_transport_*` ? **`output_stub_*` forbidden** |
| **New document body·headings** | `route_probe_start` canonical ([§0.6](#06-coordinate-terms-runtime-canonical-alias-forbidden)) |
| **Existing enum values** | `output_stub_inside_occupied` etc. ? **rename forbidden** (backward compatibility); assert via enum value·semantic mapping |

Example: `test_geometry_rejects_route_probe_start_inside_occupied` (OK) · `test_geometry_rejects_output_stub_inside_occupied` (new naming forbidden).

Details: [`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) §4 · [`open_decisions.md`](open_decisions.md) OD-1.

## Coordinates·replay (cross-reference)

- After OptimizationInput, all `Coord` = **Server X/Y** only. raw?server conversion forbidden in optimization interior.
- Replay·NDJSON·metrics are **algorithm input forbidden**.

[`asteroid_lab_00_overview.md`](../asteroid_lab_00_overview.md) · [`.cursor/rules/asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc)
