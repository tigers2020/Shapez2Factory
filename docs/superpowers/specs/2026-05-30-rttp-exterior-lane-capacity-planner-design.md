# RTTP Exterior Lane Capacity Planner (ELCP) — Design Spec

**Document type:** Canonical transport / exterior connector contract extension  
**Status:** Approved (2026-05-30 — brainstorming: Approach B + nearest = route_probe cost)  
**Work classification:** contract change · implementation change  
**Parent:** [`2026-05-26-rttp-external-void-transport-capacity-contract.md`](2026-05-26-rttp-external-void-transport-capacity-contract.md) (EVTC)  
**Recovery program:** [`2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md`](2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md)  
**Throughput CANON (numerator):** [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../../documents/game_rules/shapez2_asteroid_space_transport_throughput.md)  
**Implementation plan:** [`../plans/2026-05-30-rttp-exterior-lane-capacity-planner.md`](../plans/2026-05-30-rttp-exterior-lane-capacity-planner.md)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Korean title (reference):** RTTP 외부 lane 용량 플래너 (ELCP)

---

## §1 — Executive summary

EVTC already defines **how many** exterior connectors are required via `ceildiv(max_asteroid_throughput_per_min, transport_max_throughput_per_min)` and materializes `RouteGoal(EXTERNAL_MARGIN)` goals. Product maps still lack **throughput-aware merge**: many routes can target the same connector while **lane capacity** is not tracked, and physical belt tile count is not a capacity authority.

**ELCP** reinterprets exterior connectors as **capacity-bearing exterior transport lanes**. Each lane has a saturated Space Belt / Space Pipe capacity (EVTC denominator), a `target_load`, and running `assigned_load`. Each committed extractor/FOT route **merges into the nearest compatible lane** that still has capacity, where **nearest** means **shortest feasible `route_probe` cost** at **commit time** — never Manhattan distance as authority.

**Counting model (locked):**

```text
required_lane_count = ceildiv(max_asteroid_throughput_per_min, lane_capacity_per_min)
physical belt/pipe tile count ≠ capacity authority
EXTERNAL_MARGIN RouteGoal.coord = lane.connector_goal.coord
```

---

## §2 — Goals and non-goals

### Goals

| ID | Goal |
|----|------|
| G1 | `required_lane_count` equals EVTC `required_external_connectors` (same ceildiv; semantic rename at planner layer) |
| G2 | `sum(lane.target_load_per_min) >= max_asteroid_throughput_per_min` with each `target_load <= lane_capacity_per_min` |
| G3 | Each committed bundle has exactly one `exterior_lane_id`; `assigned_load` never exceeds `capacity_per_min` |
| G4 | Nearest merge uses commit-time `route_probe` on latest `RouteCellDomain`; tie-break chain is deterministic |
| G5 | Read-only validation emits stable `issue_code` values when lane contract breaks |
| G6 | Lane plan and assignment metrics are **output-only** (solver internal DTO → commit metrics / replay) |

### Non-goals (this slice)

| Item | Disposition |
|------|-------------|
| Min-cost max-flow / global trunk balancing | v1+ research; v0 excludes global balancing |
| Advanced corridor replacement | Out of scope |
| `final_validation` repair | Forbidden (B-CS3) |
| Mixed shape belt + fluid pipe on one lane | Forbidden |
| Replay / artifact as solver or probe input | Forbidden |
| Manhattan as merge authority | Forbidden (debug pre-sort hint only) |
| Replacing EVTC DB resolver or ceildiv function | Extend, do not fork |
| Turn / merger / splitter belt synthesis (PR-1b) | Separate slice |
| EVTC-6b `route_not_shortest_feasible` wiring | Separate slice (orthogonal path audit) |

---

## §3 — Exterior lane capacity plan (normative contract)

### §3.1 Authority split (unchanged from EVTC)

| Layer | Source | Field |
|-------|--------|-------|
| Map numerator | `build_reconstruction_capacity_envelope` + `MiningExtractionRule` | `max_asteroid_throughput_per_min` (`Decimal`) |
| Lane denominator | `transport_max_throughput_per_min(transport_kind, tier)` via `game_data` | `lane_capacity_per_min` (`Decimal`) |
| Per-candidate load | `output_per_min(rule, candidate.throughput_factor)` | `candidate_throughput_per_min` (`Decimal`) |

**Tier policy:** `ExteriorThroughputTier.TIER_1` until speed tier is plumbed (EVTC-v0 lock).

### §3.2 Required lane count

```python
from decimal import Decimal

def required_lane_count(
    *,
    max_asteroid_throughput_per_min: Decimal,
    lane_capacity_per_min: Decimal,
) -> int:
    """Semantically identical to ``required_external_connectors`` (ceildiv)."""
    ...
```

**Numeric normalization (ELCP-N1):**

```text
All throughput values remain Decimal.
All public lane/connector counts are int.
After Decimal divmod, quotient used for lane count MUST normalize to int
(e.g. int(quotient) before ceildiv increment) — never leave counts as Decimal.
```

**Invariant ELCP-1:**

```text
required_lane_count == ceildiv(max_asteroid_throughput_per_min, lane_capacity_per_min)
required_lane_count == OptimizationInput.required_external_connector_count  # when ELCP enabled
```

### §3.3 DTOs

```python
@dataclass(frozen=True, slots=True)
class ExteriorTransportLane:
    """Static capacity contract — immutable for the run after plan build."""

    lane_id: str                          # stable: exterior_lane:{kind}:{index}
    transport_kind: TransportKind
    connector_goal: RouteGoal             # goal_kind=EXTERNAL_MARGIN; coord authoritative for probe
    capacity_per_min: Decimal             # == lane_capacity_per_min for all lanes in plan
    target_load_per_min: Decimal          # full lanes: capacity; last partial: remainder
    anchor_coord: Coord                   # == connector_goal.coord in v0 (telemetry / planner spread only)


@dataclass(frozen=True, slots=True)
class ExteriorLaneAssignmentState:
    """Commit-time accumulator — separate from plan DTO."""

    lane_id: str
    assigned_load_per_min: Decimal


@dataclass(frozen=True, slots=True)
class ExteriorLaneCapacityPlan:
    transport_kind: TransportKind
    max_asteroid_throughput_per_min: Decimal
    lane_capacity_per_min: Decimal
    required_lane_count: int
    lanes: tuple[ExteriorTransportLane, ...]
```

**Responsibility split:**

```text
plan = static capacity contract (ExteriorLaneCapacityPlan + ExteriorTransportLane)
assignment_state = commit-time accumulator (tuple[ExteriorLaneAssignmentState], copy-on-write per commit step)
```

**Invariant ELCP-2 (plan shape):**

```text
len(lanes) == required_lane_count
all(lane.capacity_per_min == lane_capacity_per_min for lane in lanes)
all(lane.transport_kind == plan.transport_kind for lane in lanes)
all(lane.connector_goal.goal_kind == EXTERNAL_MARGIN for lane in lanes)
```

**Invariant ELCP-3 (target loads cover numerator):**

```python
quotient, remainder = divmod(max_asteroid_throughput_per_min, lane_capacity_per_min)
# required_lane_count = quotient if remainder == 0 else quotient + 1

for i, lane in enumerate(lanes):
    if i < len(lanes) - 1 or remainder == 0:
        assert lane.target_load_per_min == lane_capacity_per_min
    else:
        assert lane.target_load_per_min == remainder  # partial last lane only

assert sum(lane.target_load_per_min for lane in lanes) >= max_asteroid_throughput_per_min
```

When `max_asteroid_throughput_per_min <= 0` or `lane_capacity_per_min <= 0`, `required_lane_count = 0` and `lanes = ()` (same as EVTC zero guard).

### §3.4 Plan construction

**Module:** `django_apps/asteroid_lab/optimization/routing/exterior_lane_capacity_planner.py`

**Steps:**

1. Resolve `lane_capacity_per_min` via `transport_max_throughput_per_min(transport_kind, tier=TIER_1)`.
2. Compute `required_lane_count` (ceildiv).
3. Call existing `plan_exterior_connectors(..., required_count=required_lane_count)` to obtain `connector_goal` coords (spread / BFS band policy unchanged).
4. Build one `ExteriorTransportLane` per selected goal with `target_load_per_min` per ELCP-3.
5. Return `ExteriorLaneCapacityPlan`.

**Wire:** `optimization_input_from_reconstruction` sets `inp.route_goals` from plan lanes' `connector_goal` (same as today, but goals are lane-backed). Optional: attach `ExteriorLaneCapacityPlan` on pipeline commit context (not on `OptimizationInput` in v0 unless needed for validation).

**Relationship to physical tiles:** Belt/pipe cells materialized on the map are **rendering/commit path evidence**, not inputs to `required_lane_count`.

---

## §4 — Route assignment (commit-time, authoritative)

### §4.1 Nearest compatible lane (locked)

```text
nearest_compatible_lane(candidate) =
  argmin_{lane in lanes}
    route_probe_cost(
      domain = latest_route_domain_at_commit,
      start = candidate.output_stub,
      goal = lane.connector_goal.coord,
    )
  subject to:
    lane.transport_kind == candidate.transport_kind
    assignment_state[lane.lane_id].assigned_load_per_min + candidate_throughput_per_min <= lane.capacity_per_min
    probe.reachable == True
```

**Cost model:**

| Phase | Cost |
|-------|------|
| ELCP-v0 | Unweighted BFS hop count (EVTC-v0 / current `probe_route`) |
| ELCP-v1 | `RouteCellDomain.traversal_cost` weighted shortest path (EVTC-v1) |

**Manhattan distance** is never authoritative for lane assignment, validation, shortfall classification, or merge correctness. It may only be used as a **non-semantic pre-sort hint** before authoritative `route_probe` evaluation.

**Timing:** Candidate-stage probe success is **non-authoritative**. Assignment and capacity checks run inside **incremental commit** after rebuilding `RouteCellDomain` with current reservations (existing commit-time re-probe contract).

### §4.2 Assignment algorithm (per commit attempt)

```text
candidate_throughput_per_min = output_per_min(active MiningExtractionRule, candidate.throughput_factor)

compatible_lanes = [lane for lane in plan.lanes if lane.transport_kind == candidate.transport_kind]
ordered_lanes = sort by route_probe_cost ascending (unreachable lanes excluded)
apply tie-break when costs equal:
  1. lower assignment_state[lane_id].assigned_load_per_min / capacity_per_min
  2. higher connector_goal.priority
  3. lexicographic connector_goal.coord
  4. lexicographic lane_id

for lane in ordered_lanes:
    if assignment_state[lane.lane_id].assigned_load + candidate_throughput <= lane.capacity:
        assign candidate to lane (record exterior_lane_id, path evidence)
        replace assignment_state with incremented copy for lane_id
        commit route reservation to reached connector_goal.coord
        return success

return failure → lane_capacity_shortfall and/or route_feasible_shortfall (diagnostics)
```

**Commit order:** Process bundles in the **same deterministic order** `incremental_commit` already uses; lane `assigned_load` accumulates across earlier commits in that order.

### §4.3 Persisted commit evidence (output-only)

Extend `rttp.commit` metrics (JSON-safe decimals as strings):

```json
{
  "exterior_lane_plan": {
    "required_lane_count": 4,
    "lane_capacity_per_min": "2880",
    "max_asteroid_throughput_per_min": "11520"
  },
  "exterior_lane_assignments": [
    {
      "candidate_id": "c1",
      "exterior_lane_id": "exterior_lane:shape_belt:0",
      "candidate_throughput_per_min": "480",
      "route_probe_cost": 12,
      "reached_goal": [9, 7]
    }
  ]
}
```

**Forbidden:** Reading this artifact back into candidate generation, route probe, evolutionary search, or validation repair.

---

## §5 — Validation (read-only)

**Module:** extend `validate_layout_connectivity_issues` or sibling `validate_exterior_lane_contract`.

**No repair:** validation must not re-probe, reroute, reassign lanes, or mutate `commit_result`.

| Check | Condition | `issue_code` |
|-------|-----------|--------------|
| ELCP-V1 | Committed bundle lacks `exterior_lane_id` in assignment evidence | `route_without_lane_assignment` |
| ELCP-V2 | Any lane `assigned_load_per_min > capacity_per_min` | `exterior_lane_over_capacity` |
| ELCP-V3 | `sum(assigned_load) > sum(lane.capacity)` aggregate (belt kind) | `exterior_lane_over_capacity` |
| ELCP-V4 | Committed shape route assigned to fluid lane or vice versa | `exterior_lane_kind_mismatch` |
| ELCP-V5 | Distinct exterior connectors touched `< required_lane_count` when commits imply exterior export | `insufficient_exterior_connectors` (EVTC; retained) |
| ELCP-V6 | Committed > 0 but no exterior-connected route cells | `missing_exterior_route` (A6; retained) |

**Shortfall diagnostics (not always validation failures):** `lane_capacity_shortfall`, `route_feasible_shortfall` — emit in commit metrics / pipeline summary; promote to validation only when product policy requires hard fail (v0: diagnostic first, same as `placement_goal_shortfall`).

**`route_not_shortest_feasible`:** remains EVTC-6b deferred; ELCP does not block on it in v0.

New codes must be added to `django_apps/asteroid_lab/contracts/rttp_layout_issue_codes.py` and tests together.

---

## §6 — Architecture and module boundaries

```text
reconstruction_adapter
  → required_external_connectors (existing)
  → plan_exterior_connectors (existing)
  → build_exterior_lane_capacity_plan (NEW)
  → OptimizationInput.route_goals + required_external_connector_count

incremental_commit
  → rebuild RouteCellDomain
  → assign_exterior_lane_for_candidate (NEW)
  → probe_route → reserve path → update lane assigned_load

layout_connectivity_validation / validate_exterior_lane_contract
  → read-only checks on assignment evidence + lane plan
```

| Module | Responsibility |
|--------|----------------|
| `services/required_external_connectors.py` | ceildiv count only (unchanged API) |
| `routing/exterior_connector_planner.py` | Goal coord selection (unchanged policy) |
| `routing/exterior_lane_capacity_planner.py` | Plan DTO + target_load split |
| `contracts/exterior_lane_capacity.py` | Plan + assignment DTOs |
| `commit/exterior_lane_assignment.py` | Commit-time nearest-lane merge + assignment state |
| `contracts/rttp_layout_issue_codes.py` | Stable issue codes |
| `validation/layout_connectivity_validation.py` or `validate_exterior_lane_contract.py` | Read-only asserts |

**Domain layer:** pure functions for ceildiv, target_load split, lane ordering comparator — no Django I/O in domain helpers if extracted.

---

## §7 — Telemetry (recommended)

```text
external_lane_required_count
external_lane_capacity_per_min
external_lane_target_loads
external_lane_assigned_loads
external_lane_remaining_capacity
exterior_lane_over_capacity_count
nearest_lane_assignment_attempts
lane_capacity_shortfall
route_feasible_shortfall
```

---

## §8 — Forbidden shortcuts

| Forbidden | Reason |
|-----------|--------|
| Using physical exterior belt tile count as `required_lane_count` | Not capacity authority |
| Manhattan distance for merge or validation | Conflicts with EVTC shortest-feasible |
| `floor` instead of ceildiv | Under-provisions lanes |
| Hardcoded `5760` / `345600` as lane capacity SoT | DB resolver only (EVTC) |
| Mixing shape and fluid on one lane | Transport kind isolation |
| Replay-driven lane assignment | Output-only replay |
| Validation that repairs routes or reassigns lanes | B-CS3 |
| Candidate-order probe as commit proof | Existing incremental_commit contract |

---

## §9 — Testing strategy (implementation plan input)

| Layer | Tests |
|-------|-------|
| Plan DTO | ceildiv, target_load split, partial last lane, zero guards |
| Assignment | Deterministic fixture: two lanes, three candidates, capacity overflow → second lane |
| Nearest | Obstacle domain: Manhattan-preferred coord loses vs shorter probe path |
| Validation | Read-only issue codes; no mutation |
| Regression | Existing `test_required_external_connectors.py`, `test_rttp_route_goals.py` stay green |

**Order:** resolver/plan DTO → assignment unit tests → commit hook → validation → replay metrics.

---

## §10 — Approaches considered (record)

| Approach | Verdict |
|----------|---------|
| A — EVTC goal count only | Insufficient for merge/capacity |
| **B — Exterior Lane Capacity Planner** | **Approved** |
| C — Global min-cost flow | v1+; out of v0 scope |

**Nearest lane:** **Approved** — `route_probe` shortest-feasible cost at commit time (D); v0 unweighted hops; v1 weighted traversal.

---

## §11 — Parent contract alignment

| Existing contract | ELCP behavior |
|-------------------|---------------|
| EVTC ceildiv | `required_lane_count` identical |
| `RouteGoal` / `EXTERNAL_MARGIN` | One goal per lane |
| `probe_route` / commit re-probe | Authoritative for nearest |
| A6 validation | Extended, not weakened |
| Recovery design Gate B | Enables throughput-aware exterior distribution |

---

## §12 — Open follow-ons (explicitly deferred)

- ELCP-v1 weighted `traversal_cost` alignment with EVTC-v1
- EVTC-6b shortest-path validation wiring
- PR-1b turn/merger belt synthesis on shared trunk segments
- Promote `lane_capacity_shortfall` from diagnostic to hard validation fail (product gate evidence)
