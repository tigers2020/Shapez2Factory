# RTTP External Void Transport Capacity Contract (EVTC)

**Document type:** Canonical transport / route contract  
**Status:** Approved (2026-05-26)  
**Scope:** `external_void_cells` as transport-installable domain, throughput-based exterior connector count, shortest feasible routes, read-only validation  
**Not in scope:** A6 extensions (A6 remains CLOSED), placement_goal shortfall as validation failure, validation repair, replay/artifact as solver input, PR-F3–F5 decontamination  
**Parent:** [`2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md`](2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md)  
**Implementation plan:** [`docs/superpowers/plans/2026-05-26-rttp-external-void-transport-capacity-contract.md`](../plans/2026-05-26-rttp-external-void-transport-capacity-contract.md)  
**Throughput CANON:** [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../../documents/game_rules/shapez2_asteroid_space_transport_throughput.md)  
**Community reference (non-authoritative):** [shapez2.wiki.gg](https://shapez2.wiki.gg/) — must match L1 CANON; on conflict, CANON wins.

---

## §1 — Executive summary

EVTC elevates `external_void_cells` from “probe goal exceptions on blocked void” to a **transport-installable domain**. Exterior **connector** count is derived from asteroid throughput capacity using **saturated** Space Belt / Space Pipe limits, not rim-adjacent void cell count. Each committed extractor output must reach a selected exterior connector via a **shortest feasible** route under a fixed cost policy. **A6** only blocks layouts with zero output reservation / zero exterior touch; **EVTC** enforces throughput-aligned connector planning and path evidence.

---

## §2 — Boundary with A6 (Task 6, CLOSED)

| Concern | A6 (CLOSED) | EVTC |
|---------|-------------|------|
| `committed < placement_goal` | Diagnostic only (`placement_goal_shortfall`) | Unchanged |
| No output transport at all | `missing_output_transport` | Retained; may tighten definition |
| No exterior touch | `missing_exterior_route` | Retained; insufficient when connectors &lt; required |
| Connector count vs throughput | Not checked | `insufficient_exterior_connectors` |
| Path optimality | Not checked | `route_not_shortest_feasible` (v0: tie-break evidence) |
| Route repair in validation | Forbidden | Forbidden |

---

## §3 — Domain CANON

### 3.1 Void is transport-installable

```text
external_void_cells ⊆ route_domain_bbox \ occupied_snapshot_cells
external_void_cells ∩ mineable_cells = ∅
external_void_cells = belt/pipe transport-installable domain (preferred over interior shortcuts)
```

**Not CANON:** “void is blocked except goal coords.” That describes **current v0.1 implementation** until EVTC-4 lands.

### 3.2 Exterior connector

An **exterior connector** is a `RouteGoal` with `goal_kind=EXTERNAL_MARGIN` (or successor `EXTERIOR_CONNECTOR`) placed in `external_void_cells`, selected by the **exterior connector planner**, and used as a commit-time probe target for the active `TransportKind`.

### 3.3 Capacity goals vs route goals

```text
required_external_connectors = ceildiv(max_asteroid_throughput_per_min, transport_max_throughput_per_min)

capacity_goals == required_external_connectors   # product connector count
len(route_goals) may be >= capacity_goals         # planner may emit spare candidates; probe uses selected set
len(rim_adjacent_void) != capacity_goals          # forbidden identity
```

---

## §4 — Throughput inputs and saturated denominators

### 4.0 Authority split (critical)

| Layer | Source | Used for |
|-------|--------|----------|
| **Asteroid Lab reconstruction max** | `MiningExtractionRule` + field cells ([`shapez2_asteroid_space_transport_throughput.md`](../../../documents/game_rules/shapez2_asteroid_space_transport_throughput.md)) | Numerator `max_asteroid_throughput_per_min` (PR-2a) |
| **EVTC exterior transport cap** | **Shapez 2 1.0** transport metadata at selected **speed tier** (DB rows; wiki-indexed sanity) | Denominator `transport_max_throughput_per_min` |

**Shapez 2 1.0 baseline:** Official 1.0 release **2026-04-23** ([Steam 1.0 announcement](https://store.steampowered.com/news/app/2162800/view/517487885157401587), official site). Tier-1 figures below are **1.0-era wiki-indexed** regression targets; **runtime SoT = DB seed / dump-derived rows**, not wiki literals in solver code.

[`shapez2_asteroid_space_transport_throughput.md`](../../../documents/game_rules/shapez2_asteroid_space_transport_throughput.md) states wiki/community figures **do not override** Asteroid Lab L1. EVTC denominator is a **separate contract**: factory transport capacity for **one full Space Belt / Space Pipe** at the configured tier.

**EVTC-v0 tier policy (locked):** `ExteriorThroughputTier.TIER_1` — compute denominators at **belt/pipe speed tier 1** until tier is plumbed from `game_data` simulation speed tables.

**Hardcoded totals — do not use as implementation literals:**

| Value | Status |
|-------|--------|
| `5760` shapes/min | **Not tier-1.** Wiki index: tier-3 regular belt (120/min) × 48 belts. Tier-1 Space Belt cap = **2880**. |
| `345600` L/min | **Not deprecated for fluid.** Wiki-indexed tier-1: `1200 L/min` fluid launcher/port × **288** full Fluid Launchers = **345600** ([Space Transport](https://shapez2.wiki.gg/wiki/Space_Pipe), [Pipe](https://shapez2.wiki.gg/wiki/Pipe)). Distinct from Asteroid-Lab `4800 × 72` miner-saturation narrative. |

Reference only (non-authoritative): [shapez2.wiki.gg](https://shapez2.wiki.gg/). Wiki proves initial values; **정본 (canonical SoT) = `game_data` DB rows** only.

### 4.0.1 Canonical DB registration (MUST)

EVTC denominator factors **must** be formally registered in `django_apps.game_data` — same pattern as `MiningExtractionRule` (`EVTC_CANON` migration seed, partial unique active row per `speed_tier`). Solver, planner, and validation **read only** via `game_data.services.exterior_transport_capacity`; they **must not** embed `15`, `2880`, `1200`, `288`, or `345600` as literals.

| Model | Tier-1 CANON fields (DB) | Derived cap |
|-------|--------------------------|-------------|
| `ExteriorShapeTransportCapacity` | `mini_unit_output_per_min`, `buildings_per_regular_belt`, `space_belt_full_belt_count` | `space_belt_max` |
| `ExteriorFluidTransportCapacity` | `fluid_launcher_output_per_min`, `space_pipe_full_fluid_launcher_count` | `space_pipe_max` |

Changing a cap requires a **data migration** (or admin data fix policy), not a solver constant edit. Pytest asserts wiki-indexed tier-1 totals **from loaded DB rows** after migrate.

**Approval gate (2026-05-26 review, amended):**

| Kind | EVTC-1 status |
|------|----------------|
| **Shape** (`space_belt_max` @ tier 1) | **APPROVED** — EVTC-1a seed + EVTC-1b resolver |
| **Fluid** (`space_pipe_max` @ tier 1) | **APPROVED** (DB-seed verification) — same structure as shape; reject `×16×18` miner model only |

**Rejected (both kinds):** hardcoding `5760`, `345600`, `1200`, `288`, or `18` as solver SoT literals.

### 4.1 Numerator (`max_asteroid_throughput_per_min`)

**Authority:** `reconstruction_capacity.by_resource[primary].max_throughput_per_min` (decimal string in summary JSON). Same envelope as PR-2a (`build_reconstruction_capacity_envelope`). Never use replay metrics or prior `solver_summary` as input.

### 4.2 Denominator (`transport_max_throughput_per_min`) — tier-1 DB-derived

**Default policy:** `ConnectorCountPolicy.SATURATED_TRANSPORT` — one **full** exterior Space Belt or Space Pipe at the active tier.

**Primary SoT:** queryable `game_data` rows at `ExteriorThroughputTier.TIER_1`. **Never** embed literal `5760` / `345600` in solver code; derive at runtime from DB (wiki figures are test sanity only).

**Unified denominator (shape and fluid):**

```text
space_transport_max(tier) = port_rate(tier) × space_full_unit_count
```

Shape expands `port_rate` via mini-miner × buildings-per-belt; fluid uses fluid launcher/port output directly. Same resolver pattern; separate DB tables for column names.

Do **not** force shape and fluid into one identical column layout. Use **two capacity models** (separate tables or discriminated rows).

#### 4.2a Shape — **APPROVED** (Mini-Miner → Regular Belt → Space Belt)

[Mini-Miner](https://shapez2.wiki.gg/wiki/Mini-Miner): throughput tiers `15 · 22.5 · 30 · 37.5 · 45` shapes/min; **Buildings per Belt = 4**.

[Space Transport](https://shapez2.wiki.gg/wiki/Space_Pipe): Space Belt **48 full Belts** (16 per machine level, 4 per lane).

```text
mini_shape_rate(tier)           # DB: ExteriorShapeTransportCapacity.mini_unit_output_per_min
regular_belt_max(tier)          = mini_shape_rate(tier) × buildings_per_regular_belt   # 4
space_belt_max(tier)            = regular_belt_max(tier) × space_belt_full_belt_count  # 48

transport_max_throughput_per_min(SHAPE_BELT) = space_belt_max(active_tier)
```

**Tier-1 wiki sanity (regression only):**

```text
mini_shape_rate(tier=1) = 15 shapes/min
regular_belt_max = 60 shapes/min
space_belt_max(tier=1) = 2,880 shapes/min
```

#### 4.2b Fluid — **APPROVED** (Space Pipe transport ports; DB-seed verification)

**Rejected interim model:** `space_pipe_max = mini_fluid_pump_rate × 16 × 18` — conflicts with wiki Space Transport index: Space Pipe carries up to **288 full Fluid Launchers** (96 per machine level, 24 per lane).

Fluid denominator is **Space Pipe transport capacity** (`port_rate × space_full_unit_count`), not “how many full fluid miners fill a pipe.”

```text
fluid_port_rate(tier)              # DB: ExteriorFluidTransportCapacity.fluid_launcher_output_per_min
                                   # wiki tier-1 index: 1200 · 1500 · 1800 L/min (Pipe page)
space_pipe_full_launcher_count     # DB: space_pipe_full_fluid_launcher_count → wiki index 288

space_pipe_max(tier) =
    fluid_port_rate(tier) × space_pipe_full_launcher_count

transport_max_throughput_per_min(FLUID_PIPE) = space_pipe_max(active_tier)
```

**Tier-1 wiki sanity (regression only — assert from DB after seed, not solver literals):**

```text
fluid_port_rate(tier=1) = 1200 L/min
space_pipe_full_launcher_count = 288
space_pipe_max(tier=1) = 345,600 L/min
```

**EVTC-1a verification:** Seed tier-1 from DB migration; pytest asserts `1200 × 288 == 345600` from loaded rows. Optional follow-up: tiers 2–5 and dump parity (not a contract block).

**Resolver module:** `django_apps/asteroid_lab/services/rttp_exterior_transport_resolver.py`

- `space_belt_max_per_min(tier)` — **EVTC-1b**
- `space_pipe_max_per_min(tier)` — **EVTC-1b** (same `port_rate × count` pattern)

**Bridge note:** `MiningExtractionRule` remains valid for **Asteroid Lab** reconstruction numerator only.

**Non-default (future):** `ExteriorThroughputTier.MAX` · `ConnectorCountPolicy.LANE_UNIT`.

### 4.3 Required connector count (ceildiv)

```python
from decimal import Decimal

def required_external_connectors(
    *,
    max_asteroid_throughput_per_min: Decimal,
    transport_max_throughput_per_min: Decimal,
) -> int:
    if transport_max_throughput_per_min <= 0:
        return 0
    if max_asteroid_throughput_per_min <= 0:
        return 0
    # ceildiv for Decimal: ceil(a/b) without float
    q, r = divmod(max_asteroid_throughput_per_min, transport_max_throughput_per_min)
    return int(q) if r == 0 else int(q) + 1
```

Integer-only fast path (when both values are positive integers):

```python
required = (max_throughput + transport_cap - 1) // transport_cap
```

**Forbidden:** bare `//` documented as “connector count” without ceildiv semantics.

---

## §5 — Exterior connector planner

**Module:** `django_apps/asteroid_lab/optimization/routing/exterior_connector_planner.py`

**Inputs:** `OptimizationInput`, `RttpSkeleton`, `required_count`, `TransportKind`, `ReconstructionCompleteMap` bbox hints (optional).

**Output:** `ExteriorConnectorPlan` with:

- `selected_goals: tuple[RouteGoal, ...]` — length == `required_count` (or explicit shortfall flag)
- `candidate_margin_coords: frozenset[Coord]` — void coords considered
- `planner_shortfall: bool` — true when void could not place `required_count` goals

**Selection policy (EVTC-v0):** Reuse Phase C spirit from archived [`phase_c_capacity_route_goals.md`](../../../documents/Algorithm/solver_runtime/phase_c_capacity_route_goals.md):

1. Candidates in `external_void_cells` with mineable BFS distance in `[3, 5]` within `route_domain_bbox`
2. Bilateral spread on wide faces (top/bottom or left/right by aspect)
3. Even spacing along spread axis; tie-break: outermost void, then lexicographic coord
4. Cap: `min(8, max(2, required_count))` only when `required_count` would exceed 8 **and** spec explicitly allows cap — **default: no cap below `required_count`** for product maps; if cap needed, emit `connector_planner_capped` diagnostic (not validation pass)

**Wire:** `optimization_input_from_reconstruction` sets `inp.route_goals = plan.selected_goals` (not all rim-adjacent void cells).

**Skeleton:** `RttpSkeletonBuilder._capacity_goals` returns `required_external_connectors(...)` for active kind, not `ceil(platforms/12)` heuristic alone.

---

## §6 — Route domain (void traversable)

**Target (EVTC-4):** `build_route_domain_from_skeleton` treats `external_void_cells` as **traversable** for trunk-phase walk (subject to incompatible transport blocks), not as blanket `blocked_cells`.

```text
traversable_cells ⊇ (trunk_mask | lift_coords | selected_connector_coords | void_transport_walkable)
blocked_cells ⊇ mineable_cells \ platform_exceptions
```

Void transport must not be treated as mineable. Prefer exterior void edges in `traversal_cost` (EVTC-7); until then, unweighted void walk is acceptable for EVTC-4.

---

## §7 — Shortest feasible route policy

### EVTC-v0 (ship first)

- **Algorithm:** Unweighted BFS on current `RouteCellDomain` (existing `probe_route`)
- **Goal choice:** Minimum hop count to any selected connector goal; tie-break: higher `RouteGoal.priority`, then lexicographic `coord`
- **Authority:** Commit-time `probe_route` result only (candidate probe is non-authoritative)

### EVTC-v1 (follow-on)

- **Algorithm:** Weighted shortest path using `RouteCellDomain.traversal_cost`
- **Costs (initial):** void transport &lt; trunk mask &lt; interior crossover (explicit table in code)
- **Tie-break:** Lexicographic `(cost, hop_count, -priority, coord)`

---

## §8 — Commit-time path evidence

Persist per committed bundle in `rttp.commit` metrics (output-only):

```json
{
  "commit_route_evidence": [
    {
      "candidate_id": "c1",
      "reached_goal": [9, 7],
      "path_cost": 12,
      "path_length": 13,
      "path_hash": "sha256:..."
    }
  ],
  "selected_connector_coords": [[9, 7], [15, 3]],
  "required_external_connectors": 4,
  "planned_external_connectors": 4
}
```

`path_hash` is a stable hash of the coord tuple for validation replay.

---

## §9 — Validation (read-only)

Extend `validate_layout_connectivity_issues` (or sibling `validate_exterior_connector_contract`):

| Check | Issue code |
|-------|------------|
| Committed &gt; 0 and reserved routes lack output face | `missing_output_transport` (A6) |
| Committed &gt; 0 and no trunk-connected route | `missing_exterior_route` (A6) |
| `len(distinct_exterior_connectors_touched) < required_external_connectors` | `insufficient_exterior_connectors` |
| Evidence path ≠ recomputed shortest path | `route_not_shortest_feasible` |

**Forbidden:** Re-probe, reroute, or mutate `commit_result` inside validation.

---

## §10 — Forbidden shortcuts

| Forbidden | Reason |
|-----------|--------|
| Using `len(route_goals)` as connector count | Confuses margin candidates with throughput capacity |
| `floor` instead of ceildiv for required connectors | Under-provisions exterior transport |
| Default `LANE_UNIT` (480) denominator | Over-counts connectors vs saturated belt |
| Hardcoded `5760` / `345600` as primary SoT in solver code | Must derive from DB; note 5760≠tier-1 shape, 345600 may match tier-1 fluid |
| Using `max_output_per_miner × 12/72` for EVTC denominator | Conflates Asteroid Lab extraction with S2 1.0 transport metadata |
| Fluid `space_pipe_max = mini_pump × 16 × 18` | Rejected miner-saturation model |
| Literal `1200` / `288` / `345600` in solver (not DB-derived) | Same rule as shape; wiki values are test sanity only |
| Validation repair / second commit | North Star: assert only |
| Failing validation on `placement_goal_shortfall` | Product shortfall ≠ topology invalid |
| Replay / artifact as planner input | Contamination |

---

## §11 — Success evidence

Capture via `capture_rttp_recovery_evidence` after EVTC-6:

- `required_external_connectors` scalar on evidence row
- `distinct_exterior_connector_count` ≥ required (Gate EVTC-A)
- `validation_passed` true on primary Gate A slugs when transport contract satisfied
- `placement_goal_shortfall` may remain diagnostic with 62/467 commits

---

## §12 — PR train (reference)

| PR | Deliverable |
|----|-------------|
| EVTC-0 | This spec + plan + `current_plan.md` ACTIVE row |
| EVTC-1a | Tier-1 `Exterior*TransportCapacity` CANON DB + tests (**DONE**, migration `0027`) |
| EVTC-1b | Shape + fluid resolvers + ceildiv (**DONE**) |
| EVTC-2 | `exterior_connector_planner` + adapter wire |
| EVTC-3 | `probe_goal_coords` / selection = planned connectors only |
| EVTC-4 | Void traversable domain |
| EVTC-5 | Commit route evidence metrics |
| EVTC-6 | Validation issue codes + Gate tests |
| EVTC-7 | `traversal_cost` + weighted `probe_route` |

---

## §13 — Change history

| Date | Change |
|------|--------|
| 2026-05-26 | Initial CANON — Architect review: ceildiv, saturated denominator, A6 boundary, v0/v1 shortest path |
| 2026-05-26 | §4.2 amended — denominator from `MiningExtractionRule` + derived saturated cap; `5760`/`345600` regression-only |
| 2026-05-26 | §4.2 — kind-specific saturation: shape **12**, fluid **72** platforms per exterior unit (wiki/CANON); not universal ×12 |
| 2026-05-26 | §4.0–4.2 — S2 1.0 tier-1 denominator; deprecate 5760/345600 as SoT; belt×4×48 / pipe×16×18 chain from DB |
| 2026-05-26 | §4.2 split — shape APPROVED (2880 tier-1); fluid PENDING; launcher×288 model; 345600 = wiki tier-1 fluid sanity not legacy discard |
| 2026-05-26 | §4.0–4.2 — S2 1.0 release 2026-04-23; unified `port_rate × space_full_unit_count`; fluid **APPROVED** with DB-seed verification; EVTC-1b both resolvers |
| 2026-05-26 | §4.0.1 + EVTC-1a — `game_data` CANON registration (`0027`); runtime SoT = DB rows only |
| 2026-05-26 | EVTC-1b — `rttp_exterior_transport_resolver` + `required_external_connectors`; pytest flush preserves CANON tables |
