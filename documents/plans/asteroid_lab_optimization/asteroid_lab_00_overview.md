---
status: ARCHIVED
do_not_use_as_authority: true
archived_reason: plans/asteroid_lab_optimization snapshot — use documents/Algorithm/asteroid_lab_00_overview.md
authority_for_implementation: documents/Algorithm/asteroid_lab_00_overview.md
superseded_by:
  - documents/index/document_inventory.md
  - documents/ai/current_plan.md
last_reviewed: 2026-05-24
---

# Asteroid Lab Optimization — Overview


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_00_overview.md`](../../Algorithm/asteroid_lab_00_overview.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

## Role

Hybrid Optimization System Architect

## Purpose

Optimize extractor / extension / belt / pipe placement on top of completed asteroid reconstruction results.

This system is not a simple placer; it is an optimization layer with the structure:

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

## Core principles

```text
Everything is provisional until connected to exterior trunk.
```

That is, extractor / extension bundles are not confirmed placement until exterior trunk connectivity is verified.

## Coordinate space (authority)

```text
All Coord in OptimizationInput·TopologyGraph·RouteGoal·candidate·probe·commit·validation·replay = island-local (x, y).
Island map grid: integer (x, y) with `grid_contract.neighbors4`. Lab world map has no x==0 column.
```

**Sequence 12L + PR-F:** after decode/cleanup/reconstruction, algorithms use **island-local** ``(x,y)`` only. dense server bridge **removed**; ``CoordFrame.ISLAND_RAW`` is authority. copy JSON ``X==0`` valid; lab world map ``x==0`` column absent.

## Prohibitions

### 1. Replay-driven algorithm forbidden

The following data must not be used as algorithm input.

```text
NDJSON
ReplayFrame
solver_summary
debug artifact
```

These are output/debug only.

### 1b. Unified Lab replay timeline (authority)

Optimization-stage replay **appends only to `ReplayFrame` on the same `ReplayTrack`**, not a separate JSON/front track. The front uses `lab-replay-frames-data` and a **single** scrub index only. Dual-track·`optimizationReplayFrameIndex` etc. forbidden·rollback baseline: `rollback_baseline_lab_replay_timeline.md`.

### 1c. App boundary exception — output-only adapter

Default dev-sequence split:

```text
Lab replay·ORM·decode = django_apps/asteroid_lab
Optimization DTO·GA·probe·validation·replay serialization = django_apps/shapez_asteroid/optimization
```

**boundary exception: output-only adapter** — `django_apps/asteroid_lab/services/optimization_replay_to_lab_frames.py` imports `shapez_asteroid.optimization` DTO·enum to move optimization recorder `OptimizationReplayFrame` etc. to Lab `ReplayFrameAppendDTO`. **One-way (optimization → Lab append)** only; no re-injection of Lab → shapez_asteroid as algorithm input or reverse business-rule propagation.

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

### 4. Outer-rim greedy extractor installation forbidden

The following is forbidden as **pass1-class recurrence**:

```text
for rim_cell in rim_cells:
    if can_place_extractor:
        immediately confirm extractor install on layout
```

Allowed is **candidates only** — generate·probe·pool. **Selection** is Evolutionary Search; **confirmation** is Incremental Commit.

```text
Rim cells = search-space pruning for where extractor anchor candidates may sit
Rim cells ≠ install order·immediate commit rationale
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

v0 handles only:

```text
rim-only extractor candidate generation (anchor ∈ rim_cells; no immediate install·greedy pass)
linear extension pattern
shape/fluid transport kind separation
bounded uniform-cost route probe (Dijkstra-lite; same as BFS when traversal_cost=1 fixture)
bundle-level genome
mutation-only evolutionary search
best genome replay
```

**One line:** Rim is candidate anchor filter only, not install order.

## Excluded from v0

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

In v0, corridor / trunk / future expansion behavior does **not perform advanced replacement·global balancing** (same as 「Excluded from v0」 above).

However DTO·artifact·fitness breakdown **reserve those fields in advance**. Values are mostly `0`·empty sets·**conservative heuristics**.

That is, v0 does not perform advanced corridor replacement, but **schema and slots for that capability are fixed first**. Overview·Phase 1·5·7 share this policy so implementers do not drift with “field exists but unused?”.

## Contract reinforcement (review reflection, v0~v1 boundary)

For long-term solver-grade stability, the following are **documented·DTO-level prerequisites** for input·routing layers (see Phase 1·4·5·10).

```text
RouteGoal (goal_kind·priority·existing_trunk·transport)
RouteCellDomain + route_domain (prevent allowed/preferred/blocked drift)
TopologyGraph (built once at reconstruction; avoid duplicate neighbor search; undirected contract)
existing transport (coord + TransportKind) / trunk coords / protected corridor
route_domain·reservation reflection after incremental commit (Phase 7; prevent drift from candidate probe)
fitness: corridor·narrow passage·future expansion·trunk sharing·route goal quality fields
```

**Greenfield contract:** greenfield is treated only as the **special case** where `existing_transport_cells` is empty and `existing_trunk_cells`·`protected_corridor_cells` are empty sets. Optimizer does not have a greenfield-only input path·separate DTO.

Same `OptimizationInput`·same builder chain prevents **re-opening DTOs when layouts merge later**.

## Implementation survivability·architecture review summary

Architecture direction (placement+routing simultaneous evaluation, bundle-level genome, provisional→commit FSM, **replay·NDJSON output only**) removes much of v1/v2-class drift causes. Without fixing the following in **implementation phase** at doc·DTO level, **ownership·accumulated-state drift** between topology graph / `route_domain` / reservation / probe and candidate combinatorial explosion reduce survivability.

**Reinforcements to document·DTO first in v0 (priority):**

```text
1) candidate canonical dedupe — collapse equivalent geometry·stub·throughput·topology_signature candidates via CandidateEquivalenceKey etc. (Phase 3)
2) route_domain single ownership — RouteDomainSnapshotBuilder only creates snapshots; reservation·commit reflection via full rebuild, no in-place mutation (Phase 1·4·7)
3) probe optimism mitigation — predictive fragility/corridor penalties (`PenaltyMode.CONSERVATIVE`; Phase 4·5)
4) Recovery budget — thrashing caps max_removed_candidates·max_carve_cells·max_reroute_attempts etc. (Phase 7)
5) evolution diversity — forced distant mutation(**seed-stable hash**; Phase 6)
8) observed survivability — forbidden as solver/GA input (Phase 10B)
6) domain transition logging — minimal per-coord before/after route_class transition DTO when reservation changes domain (Phase 7; frozenset[Coord] alone insufficient for debug recovery)
7) validation extension — corridor residual·trunk redundancy·isolation risk: v0 minimal validation; deeper checks v1+ (Phase 8)
```

### v0 scale·Replay policy

**Premise:** in v0 where asteroid / mining **active coordinate (cell) count is roughly ≤50**, **full cell snapshot** replay per frame is sufficient. Under this premise **delta frame compression·cell reference table·shared immutable snapshot** are **not required** (optional when scaling up v1+).

Instead only **hard caps** prevent artifact·memory blow-up (Phase 9).

```text
MAX_REPLAY_CELLS_PER_FRAME = 128
MAX_REPLAY_FRAMES = 500
```

When exceeded, omit subsequent frames or truncate and record `replay_truncated: true` etc. in `metrics`.

## Trunk vs existing transport (authority)

Keep `existing_transport_cells`(coord + `TransportKind`) and `existing_trunk_cells`(coord set) **together**. **`existing_trunk_cells` is authority for trunk membership.** Do not put trunk flag on `ExistingTransportCell` (remove duplicate representation). Adapter enforces `existing_trunk_cells ⊆ coords(existing_transport_cells)` invariant.
## Sequence 12L coordinate boundary reinforcement (2026-05-17)

- Critical invariant: after decode/normalize to island grid, raw coordinates are illegal in algorithm code.
- `OptimizationInput` and later canonical coords are island-local (PR-F).
- copy JSON `X==0` is valid; not a failure condition on optimization input/candidate/route/evolution/validation/replay paths.
- copy JSON ↔ map grid re-conversion allowed only at decode/import or UI/export boundary (forbidden inside algorithm).
- `build_optimization_input` and post-inspection evolution paths use island `Coord` only; do not re-convert raw coordinates.
- **12L-hardening:** `test_import_boundaries`, `test_coordinate_frame_ast_gate`; POST `test_post_json_optimization_input_does_not_raw_convert_server_coords` (legacy test name; copy `X==0` boundary).
- UI/overlay projection changes are out of scope for 12L. If projection boundary issues are found, split to separate UI/export boundary work.
