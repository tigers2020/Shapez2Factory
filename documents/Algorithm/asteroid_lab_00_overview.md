# Asteroid Lab Optimization — Overview

> **Document baseline (2026-05-18):** Code treats **Decode → Reconstruction** as complete. Phase documents below and the checklist in [`asteroid_lab_10_development_sequence.md`](asteroid_lab_10_development_sequence.md) were **reset to not started (`[ ]`)** on the same date. References to `django_apps.shapez_asteroid` and removed test trees in the body are **historical** and may differ from the current tree. Parent guidance: [`README.md`](README.md) · [`documents/refactor_audit/00_global_summary.md`](../refactor_audit/00_global_summary.md).

## Role

Hybrid Optimization System Architect

## Purpose

Optimizes extractor / extension / belt / pipe placement on top of a completed asteroid reconstruction result.

This system is not a simple placer; it is an optimization layer with this structure:

```text
Asteroid topology
→ Local bundle pattern generation
→ Candidate expansion
→ Route feasibility probe
→ Evolutionary bundle selection
→ Incremental route commit
→ Final validation
→ Replay/debug artifact
```

## Document and checklist sync

Checkboxes in Phase contract documents `asteroid_lab_01`~`09` and sequence document `asteroid_lab_10` are **for future implementation tracking**. The canonical source for implementation and verification is **current code** and project `CANON` documents. pytest paths and listings were not updated in this folder cleanup (they may be archival citations).

## Core principles

```text
Everything is provisional until connected to exterior trunk.
```

That is, extractor / extension bundles are not confirmed placements until exterior trunk connectivity is verified.

## Coordinate space (canonical — PR-F migration)

```text
Copy JSON X/Y = island-local (paste truth).
Lab RTTP OptimizationInput.coord_frame default = ISLAND_RAW → Coord = island (x, y).
4-neighbor = grid_contract.neighbors4 on that integer grid.
```

**PR-F (2026-05, complete):** dense server `(server_x, server_y)`, `server_coords.py` bridge, replay dense projection, and persist attach **removed**. Canonical: island-local `x`/`y` only. Details: [`docs/superpowers/specs/2026-05-23-coordinate-tagged-frames-design.md`](../superpowers/specs/2026-05-23-coordinate-tagged-frames-design.md).

**Forbidden:** `server_*` coordinate tokens, `server_coords` import (`test_coordinate_frame_ast_gate`); using metrics/replay as algorithm input.

## Prohibitions

### 1. Replay-driven algorithm forbidden

The following must not be used as algorithm input:

```text
NDJSON
ReplayFrame
solver_summary
debug artifact
```

These are output/debug only.

### 2. Cell-level GA forbidden

Wrong genome:

```text
gene = cell state
```

Recommended genome:

```text
gene = placement bundle candidate
```

### 3. Routing-later pipeline forbidden

Bad structure:

```text
placement first
routing later
```

Recommended structure:

```text
candidate pool generation
+ immediate route feasibility probe
```

### 4. Outer-rim greedy extractor placement forbidden

The following is forbidden as a **pass1-style recurrence**:

```text
for rim_cell in rim_cells:
    if can_place_extractor:
        immediately commit extractor to layout
```

Only **candidates** may be generated, probed, and loaded into the pool. **Selection** is done by Evolutionary Search; **commit** is done by Incremental Commit.

```text
Rim cells = search-space pruning for extractor anchor candidate locations
Rim cells ≠ install order or immediate commit rationale
```

## Final architecture

```text
OptimizationInput
    ↓
PatternLibrary
    ↓
BundleCandidateGenerator
    ↓
FastRouteProbe
    ↓
GenomeFitnessEvaluator
    ↓
EvolutionarySearch
    ↓
IncrementalRouteCommit
    ↓
Validation
    ↓
ReplayDebugArtifact
```

## v0 scope

v0 handles only the following:

```text
rim-only extractor candidate generation (anchor ∈ rim_cells; no immediate install or greedy pass)
linear extension pattern
shape/fluid transport kind separation
bounded uniform-cost route probe (Dijkstra-lite; same as BFS when traversal_cost=1 in fixture)
bundle-level genome
mutation-only evolutionary search
best genome replay
```

**One line:** Rim is only a candidate anchor filter, not install order.

## Out of v0 scope

```text
complex extension topology
full optimal routing
CP-SAT
MILP
advanced corridor replacement
multi-objective Pareto search
global trunk balancing
```

## v0 field policy

In v0, corridor / trunk / future expansion behavior does **not** perform advanced replacement or global balancing (same as 「Out of v0 scope」 above).

However, DTOs, artifacts, and fitness breakdown **reserve those fields in advance**. Values are mostly filled with `0`, empty sets, or **conservative heuristics**.

That is, v0 does not perform advanced corridor replacement, but **fixes the slot and schema where that capability will land**. This document and Phase 1·5·7 assume the same policy so implementers do not drift with 「the field exists but why isn't it used?」.

## Contract reinforcement (review feedback, v0~v1 boundary)

For long-term solver-grade stability, the following are **documented and fixed at DTO level first** in the input and routing layers (see Phase 1·4·5·10):

```text
RouteGoal (goal_kind·priority·existing_trunk·transport)
RouteCellDomain + route_domain (prevent allowed/preferred/blocked drift)
TopologyGraph (built once at reconstruction; avoid duplicate neighbor search; undirected contract)
existing transport (coord + TransportKind) / trunk coords / protected corridor
route_domain and reservation reflection after incremental commit (Phase 7; prevent drift vs candidate probe)
fitness: corridor·narrow passage·future expansion·trunk sharing·route goal quality fields
```

**Greenfield contract:** greenfield is treated only as the **special case** where `existing_transport_cells` is empty and `existing_trunk_cells`·`protected_corridor_cells` are empty sets. The optimizer does not use a greenfield-only input path or separate DTO.

The same `OptimizationInput` and builder chain must be used to **avoid reopening DTOs later during layout integration**.

## Implementation survivability and architecture review summary

The architecture direction (placement+routing co-evaluation, bundle-level genome, provisional→commit FSM, **replay·NDJSON output only**) removes much of the drift seen in earlier v1/v2-style work. However, if the following are not fixed in docs and DTOs during **implementation**, survivability drops due to **ownership and accumulated-state drift** between topology graph / `route_domain` / reservation / probe and candidate combinatorial explosion.

**Reinforcements to document and DTO ahead in v0 (priority):**

```text
1) candidate canonical dedupe — reduce identical geometry·stub·throughput·topology_signature candidates via equivalence keys such as CandidateEquivalenceKey (Phase 3)
2) route_domain single ownership — RouteDomainSnapshotBuilder only creates snapshots; reservation·commit reflection via full rebuild, no in-place mutation (Phase 1·4·7)
3) probe optimism handling — candidate-time reachable ≠ commit-time corridor starvation; fitness uses **predictive** conservative proxies such as route_fragility·shared corridor pressure (`PenaltyMode.CONSERVATIVE`; Phase 4·5)
4) Recovery budget — thrashing caps such as max_removed_candidates·max_carve_cells·max_reroute_attempts (Phase 7)
5) evolution diversity — GenomeDiversityMetrics (log·replay metrics)·forced distant mutation (**seed-stable hash**; Phase 6)
8) observed survivability — `CommitSurvivabilityMetrics`·replay summary are **observation only**; solver·GA·fitness evaluator **must not read them** (Phase 10B)
6) domain transition record — minimal per-coord before/after route_class transition DTO when reservation changes domain (Phase 7; frozenset[Coord] alone is insufficient for debug recovery)
7) validation expansion — v0 keeps minimal checks for corridor remainder·trunk duplication·isolation risk; deeper checks in v1+ (Phase 8)
```

### v0 scale and replay policy

**Assumption:** For v0 with roughly **≤50 active coordinates (cells)** on asteroid / mining layouts, **full cell snapshot** replay per frame is sufficient. Under this assumption, **delta frame compression·cell reference tables·immutable snapshot sharing** are **not required** (optional at v1+ scale-up).

Instead, only **hard caps** are applied to prevent artifact and memory blow-up (Phase 9).

```text
MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME = 128
MAX_OPTIMIZATION_REPLAY_FRAMES = 500
MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME = 2000
MAX_LAB_REPLAY_TIMELINE_FRAMES = 500
```

Canonical module: `django_apps/asteroid_lab/replay/replay_limits.py`.

When exceeded, omit or truncate subsequent frames and record `replay_truncated: true` etc. in `metrics`.

## Trunk vs existing transport (canonical)

Keep `existing_transport_cells` (coord + `TransportKind`) and `existing_trunk_cells` (coord set) **together**. **Canonical trunk membership is `existing_trunk_cells`**. Do not put a trunk flag on `ExistingTransportCell` (avoid duplicate representation). The adapter enforces `existing_trunk_cells ⊆ coords(existing_transport_cells)`.

## GameData snapshot (ADR-004)

Asteroid Lab consumes normalized building and transport data via a **revision-pinned snapshot**, not live ORM in the solver path.

| Reference | Content |
|-----------|---------|
| [ADR-004: game_data snapshot boundary](../../docs/adr/ADR-004-game-data-snapshot-boundary.md) | `game_data` selectors/builder → `web` assembler → `asteroid_lab` adapter; `default` DB only in v0 |
| [Asteroid game_data snapshot (domain)](../../docs/domain/asteroid_game_data_snapshot.md) | `AsteroidGameDataSnapshot`, `SnapshotMeta`, canonical row order |
| [Coord transform spec](../../docs/domain/asteroid_coord_transform_spec.md) | Server X/Y after decode; no raw coords in optimization |
| [Deploy runbook](../../docs/runbooks/game_data_snapshot_deploy.md) | `import_game_data --verify`, pytest gate, rolling deploy |

**v0 rule:** snapshot meta in `SolverRun.config_json` is provenance only until PatternLibrary / solver-input ADR approves algorithm use.

## Sequence 12L coordinate boundary reinforcement (2026-05-17)

- Critical invariant: after decode/import normalization produces Server X/Y, raw coordinates are illegal in algorithm code.
- After `OptimizationInput`, the canonical algorithm-layer coordinates are Server X/Y dense grid.
- **Island-local:** copy JSON `X==0` valid; lab world map has no `x==0` column — do not mix frames.
- `build_optimization_input` and post-inspection evolution consume **island `Coord` only**; raw↔dense server re-conversion **forbidden**.
- **Hardening:** `tests/unit/asteroid_lab/test_coordinate_frame_ast_gate.py` (forbidden tokens `server_x`/`server_coords`/…); `tests/unit/shapez_asteroid/test_import_boundaries.py`; POST `test_post_json_optimization_input_does_not_raw_convert_server_coords` (legacy name — asserts no raw bridge at optimization boundary).
- UI/overlay projection changes are out of scope for 12L. If a projection boundary issue is found, split it into a separate UI/export boundary task.
