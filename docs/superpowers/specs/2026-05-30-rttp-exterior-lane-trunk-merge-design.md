# RTTP Exterior Lane Trunk Merge (ELCP-TM) — Design Spec

**Document type:** Canonical transport / commit geometry extension  
**Status:** Approved (2026-05-30 — §1·§2 conditional OK + architect corrections)  
**Work classification:** contract change · implementation change  
**Parent:** [`2026-05-30-rttp-exterior-lane-capacity-planner-design.md`](2026-05-30-rttp-exterior-lane-capacity-planner-design.md) (ELCP)  
**Throughput CANON:** [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../../documents/game_rules/shapez2_asteroid_space_transport_throughput.md)  
**Implementation plan:** [`../plans/2026-05-30-rttp-exterior-lane-trunk-merge.md`](../plans/2026-05-30-rttp-exterior-lane-trunk-merge.md)

**Korean title (reference):** RTTP 외부 lane 공유 trunk 병합 (ELCP-TM)

---

## §1 — Executive summary

ELCP v0 correctly tracks **how many** exterior lanes (`required_lane_count` via ceildiv) and **per-lane throughput** (`assigned_load_per_min`), but commit still reserves **per-candidate parallel void corridors** (output spine + full probe path union). Lab maps therefore show **one belt column per extractor**, which violates the product rule:

```text
All extractors merge onto one exterior belt until that lane saturates,
then a second belt appears, and so on, up to required_lane_count.
```

**ELCP-TM** adds:

1. **Fill-first lane activation** — only the lowest-index **non-saturated** active lane may receive commits; the next lane activates **only** when the current fill lane cannot accept the candidate's throughput (capacity exhausted), **never** because a later lane is route-closer or reachable while the current lane still has capacity.
2. **Per-lane shared trunk** — one reusable `trunk_cells` set per active `lane_id`; new commits reserve **`branch_cells` only**; `reused_trunk_cells` appear in evidence but do not re-trigger private-route conflict.

**Capacity authority unchanged:** `lane_capacity_per_min` MUST come from `transport_max_throughput_per_min(...)` (game_data resolver). Values such as 480 or 2880 are fixture examples only — **no hardcoded lane capacity in implementation**.

---

## §2 — Goals and non-goals

### Goals

| ID | Goal |
|----|------|
| TM-G1 | Visual / reservation evidence: at most **one shared trunk corridor per active lane** on void; stubs attach via short branches |
| TM-G2 | Fill-first: lane `i+1` has `assigned_load > 0` only after lane `i` cannot accept `candidate_throughput` (capacity), with activation evidence |
| TM-G3 | Route-unreachable on current fill lane while capacity remains → **`route_feasible_shortfall`**; **no** premature lane activation |
| TM-G4 | `reserved_route_cells` growth dominated by `branch_cells` + first-trunk establishment, not duplicate parallel void highways |
| TM-G5 | Read-only validation for premature activation, trunk connectivity, branch-to-trunk attachment |
| TM-G6 | Metrics / assignment rows include trunk + activation evidence (output-only; forbidden as solver input) |

### Non-goals

| Item | Disposition |
|------|-------------|
| Replacing `required_lane_count` / EVTC ceildiv | Unchanged (ELCP) |
| Nearest-lane among all non-full lanes (ELCP §4.1) | **Superseded** by fill-first when ELCP-TM enabled |
| PR-1b turn / merger / splitter belt **tile synthesis** | Separate slice; TM may use straight cells only in v0 |
| Min-cost flow / global trunk balancing | v1+ |
| Replay / artifact as probe input | Forbidden |
| Physical belt tile count as capacity authority | Forbidden |

---

## §3 — Fill-first lane activation (normative)

### §3.1 Active lane set

```text
active_lane_count := 1 if required_lane_count >= 1 else 0
lanes[0 .. required_lane_count-1] exist in ExteriorLaneCapacityPlan (static)
only lanes with index < active_lane_count are "active" for probe, reservation, overlay
```

### §3.2 Per-candidate algorithm (deterministic commit order)

```text
candidate_throughput = output_per_min(active MiningExtractionRule, candidate.throughput_factor)

current_lane = lanes[lowest index L among active lanes where
  assignment_state[L].assigned_load + candidate_throughput <= lanes[L].capacity_per_min]

If no current_lane (all active lanes saturated):
  if active_lane_count < required_lane_count:
    active_lane_count += 1
    current_lane = newly activated lane
    record activation evidence (reason = capacity_exhausted)
  else:
    fail lane_capacity_shortfall

Probe goals for current_lane:
  if trunk_state[L].trunk_cells non-empty:
    goals = trunk_state[L].trunk_cells ∪ {connector_coord}
  else:
    goals = {connector_coord}

probe = route_probe(domain, start=probe_start, goals=goals, ...)

If probe reaches connector OR any trunk cell on current_lane:
  assign to current_lane; update branch/trunk reservation (§4)
Else if current_lane still has capacity for candidate_throughput:
  fail route_feasible_shortfall
  DO NOT activate lane L+1
Else:
  # capacity exhausted on current_lane — activation path (same as "no current_lane" branch)
  activate next lane if allowed; else lane_capacity_shortfall
```

### §3.3 Activation vs reachability (locked table)

| Situation | Outcome |
|-----------|---------|
| Lane0 capacity OK + reachable | Assign lane0 |
| Lane0 capacity OK + unreachable | **`route_feasible_shortfall`**; lane1 **forbidden** |
| Lane0 capacity insufficient | Activate lane1 (if `active_lane_count < required_lane_count`) |
| Lane0 saturated + lane1 reachable | Assign lane1 |
| All lanes saturated | `lane_capacity_shortfall` |

**Forbidden:** Activating lane `i+1` because lane `i` is unreachable while lane `i` still has remaining capacity.

### §3.4 Tie-break (within same current_lane only)

When multiple probe goals tie (trunk attachment vs connector), use existing deterministic chain:

```text
route_probe_cost → connector_goal.priority → lex coord → lane_id
```

Lane index ordering is **not** a tie-break across lanes — fill-first picks the lane before probing.

---

## §4 — Shared trunk reservation

### §4.1 DTOs

```python
@dataclass(frozen=True, slots=True)
class ExteriorLaneTrunkState:
    lane_id: str
    transport_kind: TransportKind
    active: bool
    assigned_load_per_min: Decimal
    trunk_cells: frozenset[Coord]
    connector_coord: Coord


@dataclass(frozen=True, slots=True)
class ExteriorLaneRouteEvidence:
    candidate_id: str
    lane_id: str
    candidate_throughput_per_min: Decimal
    branch_cells: tuple[Coord, ...]
    reused_trunk_cells: tuple[Coord, ...]
    new_trunk_cells: tuple[Coord, ...]
    reached_connector_coord: Coord | None
    reached_trunk_coord: Coord | None


@dataclass(frozen=True, slots=True)
class ExteriorLaneActivationEvidence:
    activated_lane_id: str
    previous_lane_id: str
    previous_lane_assigned_load_per_min: Decimal
    previous_lane_capacity_per_min: Decimal
    trigger_candidate_id: str
    trigger_candidate_throughput_per_min: Decimal
    activation_reason: str  # enum: capacity_exhausted only in v0
```

**Responsibility split (unchanged + TM):**

| DTO | Responsibility |
|-----|----------------|
| `ExteriorLaneCapacityPlan` | Max lanes, capacities, connector goals (static) |
| `ExteriorLaneAssignmentState` | Per-lane `assigned_load_per_min` (may mirror trunk state load; single source: assignment tuple) |
| `ExteriorLaneTrunkState` | Active flag + shared geometry per lane |
| `ExteriorLaneRouteEvidence` | Per-commit branch/trunk delta evidence |
| `ExteriorLaneActivationEvidence` | Lane open events |

### §4.2 Reservation semantics

```text
lane.trunk_cells are shareable for same transport_kind and same lane_id.

On successful commit to lane L:
  reused_trunk_cells = path cells already in trunk_state[L].trunk_cells (before update), path order
  If trunk_state[L].trunk_cells empty (first commit on lane):
    branch_cells = ()
    new_trunk_cells = full probe path (establishes trunk)
  Else:
    branch_cells = path prefix from probe_start until first cell in trunk_cells (cells not yet in trunk)
    new_trunk_cells = ()  # v0: no promotion of branch into trunk on reuse commits
  reserved_route_cells_delta = branch_cells ∪ new_trunk_cells only

  reserved_route_cells_delta = branch_cells ∪ new_trunk_cells
  DO NOT re-insert reused_trunk_cells into committed_route_cells if already present

Conflict policy (_private_route_cell_overlap):
  overlap with committed_route_cells is allowed when cell ∈ shareable_trunk_cells
  shareable_trunk_cells = ⋃_{active lanes L} trunk_state[L].trunk_cells
```

### §4.3 Output spine (TM guard)

When ELCP-TM is active, `_augment_route_cells_with_output_spine` MUST NOT extend a parallel void highway beyond the **first attachment** to `shareable_trunk_cells` for the assigned lane. Stub→trunk attachment only.

---

## §5 — Validation, metrics, architecture boundaries

### §5.1 New issue codes

Add to `rttp_layout_issue_codes.py` (with tests):

| Code | Condition |
|------|-----------|
| `exterior_lane_premature_activation` | Lane `i+1` has `assigned_load > 0` while lane `i` `remaining_capacity >= trigger_candidate_throughput` at activation time (evidence-based) |
| `exterior_lane_trunk_not_shared` | Same `lane_id`: committed trunk evidence disconnected |
| `exterior_lane_branch_not_connected_to_trunk` | `branch_cells` not adjacent to `reused_trunk_cells ∪ new_trunk_cells` when trunk non-empty |

**Retained:** `exterior_lane_over_capacity`, `route_without_lane_assignment`, `exterior_lane_kind_mismatch`, EVTC codes.

### §5.2 Commit metrics (output-only extension)

```json
{
  "exterior_lane_activations": [
    {
      "activated_lane_id": "exterior_lane:shape_belt:1",
      "previous_lane_id": "exterior_lane:shape_belt:0",
      "activation_reason": "capacity_exhausted",
      "previous_lane_assigned_load_per_min": "2880.0",
      "previous_lane_capacity_per_min": "2880.0"
    }
  ],
  "exterior_lane_route_evidence": [
    {
      "candidate_id": "c1",
      "lane_id": "exterior_lane:shape_belt:0",
      "branch_cells": [[1, 0]],
      "reused_trunk_cells": [],
      "new_trunk_cells": [[1,0],[1,1],[1,2]]
    }
  ]
}
```

### §5.3 Module boundaries

```text
exterior_lane_capacity.py          — add TM DTOs
commit/exterior_lane_fill_first.py — NEW: current lane selection, activation policy
commit/exterior_lane_trunk.py      — NEW: trunk state transitions, branch/trunk split
commit/exterior_lane_assignment.py — deprecate nearest-all-lanes; re-export or thin wrapper
commit/incremental_commit.py       — TM hook: trunk state loop, shareable trunk overlap
validation/validate_exterior_lane_contract.py — TM checks
```

**ELCP planner / ceildiv:** unchanged.

**PR-1b:** TM delivers merged **reservation geometry**; merger tiles remain optional later.

### §5.4 Feature gate

When `exterior_lane_plan` is present and `required_lane_count > 0`, **ELCP-TM replaces** ELCP v0 nearest-lane assignment. No separate feature flag in v0.

### §5.5 Invariants

| ID | Invariant |
|----|-----------|
| TM-1 | `active_lane_count <= required_lane_count` |
| TM-2 | `assigned_load(lane_i) > 0` for `i > 0` implies activation evidence exists with `activation_reason == capacity_exhausted` |
| TM-3 | For any commit while lane `i` has capacity for candidate: `lane_id <= i` (no higher index) |
| TM-4 | `sum(assigned_load) <= sum(capacity)` per plan (ELCP retained) |
| TM-5 | `len(reused_trunk_cells ∩ new_trunk_cells) == 0` per evidence row |

---

## §6 — Testing strategy (spec-level)

| Layer | Focus |
|-------|--------|
| Pure | Fill-first selection, activation guard, branch/trunk partition |
| Assignment | Unreachable lane0 + capacity → no lane1; saturated lane0 → lane1 |
| Commit integration | `reserved_route_cells` does not grow N parallel north columns for N miners on one lane |
| Validation | Premature activation, disconnected trunk |

Use **fixture** `lane_capacity_per_min` values; assert resolver wiring via mock only in planner tests (existing ELCP).

---

## §7 — Relationship to ELCP v0 spec

| ELCP v0 § | TM disposition |
|-----------|----------------|
| §4.1 nearest compatible lane | **Superseded** by §3 fill-first |
| §4.2 assignment algorithm | Replaced by §3–§4 |
| §4.3 metrics | Extended (§5.2) |
| §5 validation | Extended (§5.1) |
| Plan build / ceildiv | Unchanged |

Parent ELCP document remains historical authority for plan DTOs; on conflict for **assignment policy**, **this document wins**.
