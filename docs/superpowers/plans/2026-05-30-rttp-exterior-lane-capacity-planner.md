# RTTP Exterior Lane Capacity Planner (ELCP) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend EVTC so exterior connectors are **capacity-bearing lanes** with commit-time **route_probe nearest** merge, read-only validation, and output-only metrics — without using physical belt tile count as capacity authority.

**Architecture:** Static `ExteriorLaneCapacityPlan` (immutable lanes + target loads) + mutable-through-replacement `ExteriorLaneAssignmentState` during `incremental_commit`. `required_lane_count` reuses `required_external_connectors` ceildiv. Lane goal selection stays on `plan_exterior_connectors`; per-candidate assignment probes each lane's `connector_goal.coord` on latest `RouteCellDomain`.

**Tech Stack:** Python 3.12+, Django 5.2, `Decimal`, RTTP (`reconstruction_adapter`, `incremental_commit`, `probe_route`, `validate_layout_connectivity_issues`), `MiningExtractionRule` via `game_data.services.mining_extraction_rules.output_per_min`, pytest, ruff, mypy (`django_apps/asteroid_lab`).

**Canonical spec:** [`docs/superpowers/specs/2026-05-30-rttp-exterior-lane-capacity-planner-design.md`](../specs/2026-05-30-rttp-exterior-lane-capacity-planner-design.md)

**Parent:** [`docs/superpowers/specs/2026-05-26-rttp-external-void-transport-capacity-contract.md`](../specs/2026-05-26-rttp-external-void-transport-capacity-contract.md)

---

## File map (create / modify)

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/contracts/exterior_lane_capacity.py` | `ExteriorTransportLane`, `ExteriorLaneAssignmentState`, `ExteriorLaneCapacityPlan` |
| `django_apps/asteroid_lab/optimization/routing/exterior_lane_capacity_helpers.py` | Pure: `lane_target_loads`, `initial_assignment_state`, int-normalized ceildiv wrapper |
| `django_apps/asteroid_lab/optimization/routing/exterior_lane_capacity_planner.py` | `build_exterior_lane_capacity_plan` |
| `django_apps/asteroid_lab/optimization/commit/exterior_lane_assignment.py` | Nearest-lane ordering, probe-per-lane, assignment state updates |
| `django_apps/asteroid_lab/optimization/commit/incremental_commit.py` | Hook assignment when plan present; optional `CommitConflictReason` |
| `django_apps/asteroid_lab/optimization/reconstruction_adapter.py` | Build plan; wire `route_goals` from lanes |
| `django_apps/asteroid_lab/optimization/pipeline.py` | Pass plan into commit; emit metrics on `rttp.commit` step |
| `django_apps/asteroid_lab/contracts/rttp_layout_issue_codes.py` | ELCP issue codes |
| `django_apps/asteroid_lab/optimization/validation/validate_exterior_lane_contract.py` | Read-only lane checks |
| `django_apps/asteroid_lab/optimization/validation/layout_connectivity_validation.py` | Delegate or import lane validator |
| `tests/unit/asteroid_lab/test_exterior_lane_capacity_helpers.py` | Pure helper tests |
| `tests/unit/asteroid_lab/test_exterior_lane_capacity_planner.py` | Plan build tests |
| `tests/unit/asteroid_lab/test_exterior_lane_assignment.py` | Assignment ordering / capacity |
| `tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py` | Validation read-only |
| `documents/ai/current_plan.md` | ACTIVE ELCP row |

---

### Task 0: Docs queue (plan + spec linkage)

**Files:**
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/specs/2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md` (§ pointer, optional)

- [ ] **Step 1: Add ACTIVE row to `current_plan.md`**

```markdown
**ACTIVE — ELCP** — Exterior Lane Capacity Planner (EVTC extension). **NEXT: Task 1** DTO/helpers. Spec: [`2026-05-30-rttp-exterior-lane-capacity-planner-design.md`](../specs/2026-05-30-rttp-exterior-lane-capacity-planner-design.md). Plan: [`2026-05-30-rttp-exterior-lane-capacity-planner.md`](2026-05-30-rttp-exterior-lane-capacity-planner.md).
```

- [ ] **Step 2: Commit (when user requests)**

```bash
git add docs/superpowers/specs/2026-05-30-rttp-exterior-lane-capacity-planner-design.md docs/superpowers/plans/2026-05-30-rttp-exterior-lane-capacity-planner.md documents/ai/current_plan.md
git commit -m "docs(rttp): add ELCP design spec and implementation plan"
```

---

### Task 1: ELCP DTOs + pure helpers

**Work classification:** contract change

**Files:**
- Create: `django_apps/asteroid_lab/contracts/exterior_lane_capacity.py`
- Create: `django_apps/asteroid_lab/optimization/routing/exterior_lane_capacity_helpers.py`
- Create: `tests/unit/asteroid_lab/test_exterior_lane_capacity_helpers.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/asteroid_lab/test_exterior_lane_capacity_helpers.py
from decimal import Decimal

from django_apps.asteroid_lab.optimization.routing.exterior_lane_capacity_helpers import (
    lane_target_loads_per_min,
    normalize_required_lane_count,
)


def test_normalize_required_lane_count_ceildiv_shape_two_lanes() -> None:
    assert (
        normalize_required_lane_count(
            max_asteroid_throughput_per_min=Decimal("5760"),
            lane_capacity_per_min=Decimal("2880"),
        )
        == 2
    )


def test_lane_target_loads_partial_last_lane() -> None:
    loads = lane_target_loads_per_min(
        max_asteroid_throughput_per_min=Decimal("5760"),
        lane_capacity_per_min=Decimal("2880"),
        required_lane_count=2,
    )
    assert loads == (Decimal("2880"), Decimal("2880"))


def test_lane_target_loads_remainder_on_last_lane_only() -> None:
    loads = lane_target_loads_per_min(
        max_asteroid_throughput_per_min=Decimal("3000"),
        lane_capacity_per_min=Decimal("2880"),
        required_lane_count=2,
    )
    assert loads == (Decimal("2880"), Decimal("120"))
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_capacity_helpers.py -v`  
Expected: `ModuleNotFoundError` or import failure

- [ ] **Step 3: Implement DTOs**

```python
# django_apps/asteroid_lab/contracts/exterior_lane_capacity.py
@dataclass(frozen=True, slots=True)
class ExteriorTransportLane:
    lane_id: str
    transport_kind: TransportKind
    connector_goal: RouteGoal
    capacity_per_min: Decimal
    target_load_per_min: Decimal
    anchor_coord: Coord


@dataclass(frozen=True, slots=True)
class ExteriorLaneAssignmentState:
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

- [ ] **Step 4: Implement helpers**

```python
# exterior_lane_capacity_helpers.py
def normalize_required_lane_count(
    *,
    max_asteroid_throughput_per_min: Decimal,
    lane_capacity_per_min: Decimal,
) -> int:
    if lane_capacity_per_min <= 0 or max_asteroid_throughput_per_min <= 0:
        return 0
    quotient, remainder = divmod(max_asteroid_throughput_per_min, lane_capacity_per_min)
    q = int(quotient)
    return q if remainder == 0 else q + 1


def lane_target_loads_per_min(
    *,
    max_asteroid_throughput_per_min: Decimal,
    lane_capacity_per_min: Decimal,
    required_lane_count: int,
) -> tuple[Decimal, ...]:
    if required_lane_count <= 0:
        return ()
    _, remainder = divmod(max_asteroid_throughput_per_min, lane_capacity_per_min)
    loads: list[Decimal] = []
    for index in range(required_lane_count):
        is_last = index == required_lane_count - 1
        if is_last and remainder != 0:
            loads.append(remainder)
        else:
            loads.append(lane_capacity_per_min)
    return tuple(loads)
```

- [ ] **Step 5: Run tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_capacity_helpers.py -v`  
Run: `python -m ruff check django_apps/asteroid_lab/contracts/exterior_lane_capacity.py django_apps/asteroid_lab/optimization/routing/exterior_lane_capacity_helpers.py tests/unit/asteroid_lab/test_exterior_lane_capacity_helpers.py`

- [ ] **Step 6: Commit (when user requests)**

```bash
git add django_apps/asteroid_lab/contracts/exterior_lane_capacity.py django_apps/asteroid_lab/optimization/routing/exterior_lane_capacity_helpers.py tests/unit/asteroid_lab/test_exterior_lane_capacity_helpers.py
git commit -m "feat(rttp): add ELCP plan DTOs and lane target-load helpers"
```

---

### Task 2: Planner construction from EVTC connector goals

**Work classification:** implementation change

**Depends on:** Task 1

**Files:**
- Create: `django_apps/asteroid_lab/optimization/routing/exterior_lane_capacity_planner.py`
- Create: `tests/unit/asteroid_lab/test_exterior_lane_capacity_planner.py`
- Modify: `django_apps/asteroid_lab/optimization/reconstruction_adapter.py`

- [ ] **Step 1: Write failing planner test**

```python
@pytest.mark.django_db
def test_build_plan_lane_count_matches_required_connectors(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    inp = _minimal_inp_with_void_cells()  # fixture helper in test file
    plan = build_exterior_lane_capacity_plan(
        inp,
        max_asteroid_throughput_per_min=Decimal("5760"),
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert plan.required_lane_count == 2
    assert len(plan.lanes) == 2
    assert plan.lanes[0].lane_id == "exterior_lane:shape_belt:0"
    assert plan.lanes[0].connector_goal.goal_kind == RouteGoalKind.EXTERNAL_MARGIN
    assert sum(lane.target_load_per_min for lane in plan.lanes) >= Decimal("5760")
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_capacity_planner.py -v`

- [ ] **Step 3: Implement `build_exterior_lane_capacity_plan`**

```python
def build_exterior_lane_capacity_plan(
    inp: OptimizationInput,
    *,
    max_asteroid_throughput_per_min: Decimal,
    transport_kind: TransportKind,
    tier: ExteriorThroughputTier = ExteriorThroughputTier.TIER_1,
) -> ExteriorLaneCapacityPlan:
    lane_capacity = transport_max_throughput_per_min(transport_kind, tier=tier)
    required = normalize_required_lane_count(
        max_asteroid_throughput_per_min=max_asteroid_throughput_per_min,
        lane_capacity_per_min=lane_capacity,
    )
    connector_plan = plan_exterior_connectors(
        inp, required_count=required, transport_kind=transport_kind
    )
    target_loads = lane_target_loads_per_min(
        max_asteroid_throughput_per_min=max_asteroid_throughput_per_min,
        lane_capacity_per_min=lane_capacity,
        required_lane_count=required,
    )
    lanes = tuple(
        ExteriorTransportLane(
            lane_id=f"exterior_lane:{transport_kind.value}:{index}",
            transport_kind=transport_kind,
            connector_goal=goal,
            capacity_per_min=lane_capacity,
            target_load_per_min=target_loads[index],
            anchor_coord=goal.coord,
        )
        for index, goal in enumerate(connector_plan.selected_goals)
    )
    return ExteriorLaneCapacityPlan(...)
```

Assert `len(lanes) == required` or set `planner_shortfall` diagnostic on connector plan shortfall (reuse `ExteriorConnectorPlan.planner_shortfall` in metrics only).

- [ ] **Step 4: Wire `optimization_input_from_reconstruction`**

After `required_external_connectors` call, build plan; set `route_goals` to tuple of `lane.connector_goal for lane in plan.lanes` (preserve order). Return plan via new optional out-parameter or tuple return only in pipeline layer — **prefer** storing plan on `PipelineResult` / local variable in `_run_v01_rttp_pipeline`, not on `OptimizationInput` v0.

- [ ] **Step 5: Run tests + regression**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_capacity_planner.py tests/unit/asteroid_lab/test_required_external_connectors.py tests/unit/asteroid_lab/test_optimization_input_adapter.py -v`

- [ ] **Step 6: Commit (when user requests)**

```bash
git commit -m "feat(rttp): build exterior lane capacity plan from EVTC goals"
```

---

### Task 3: Commit-time lane assignment (unit tests, no pipeline hook yet)

**Work classification:** contract change · implementation change

**Depends on:** Task 1

**Files:**
- Create: `django_apps/asteroid_lab/optimization/commit/exterior_lane_assignment.py`
- Create: `tests/unit/asteroid_lab/test_exterior_lane_assignment.py`

- [ ] **Step 1: Write failing assignment tests**

Cover:
1. Two lanes, candidate fits lane 0 → assigns lane 0.
2. Lane 0 at capacity, lane 1 reachable with lower cost than exhausted lane 0 → lane 1.
3. Obstacle fixture: Manhattan-nearer goal unreachable; farther goal wins on probe cost.
4. Tie-break: equal cost → lower `assigned_load / capacity` ratio.

Use small hand-built `RouteCellDomain` (pattern from `tests/unit/asteroid_lab/test_route_probe*.py` if present).

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_assignment.py -v`

- [ ] **Step 3: Implement `select_exterior_lane_for_candidate`**

```python
@dataclass(frozen=True, slots=True)
class ExteriorLaneSelection:
    lane_id: str
    connector_coord: Coord
    route_probe_cost: int
    probe: RouteProbeResult


def select_exterior_lane_for_candidate(
    candidate: BundleCandidate,
    *,
    plan: ExteriorLaneCapacityPlan,
    assignment_state: tuple[ExteriorLaneAssignmentState, ...],
    domain: RouteCellDomain,
    candidate_throughput_per_min: Decimal,
    probe_start: Coord,
    max_expansions: int,
) -> ExteriorLaneSelection | None:
    """Probe each lane goal; return best per spec or None (shortfall)."""
```

Implementation notes:
- Load `assigned_by_lane_id` dict from `assignment_state`.
- For each lane: single-goal `probe_route(domain, probe_start, frozenset({goal.coord}), ...)`.
- Skip unreachable; skip `assigned + throughput > capacity`.
- Sort by `(cost, load_ratio, -priority, coord, lane_id)`.
- **Do not** use Manhattan for ordering except optional pre-sort before probe list.

- [ ] **Step 4: Implement `increment_assignment_state` (immutable update)**

```python
def increment_assignment_state(
    state: tuple[ExteriorLaneAssignmentState, ...],
    *,
    lane_id: str,
    delta: Decimal,
) -> tuple[ExteriorLaneAssignmentState, ...]:
    ...
```

- [ ] **Step 5: Run tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_assignment.py -v`

- [ ] **Step 6: Commit (when user requests)**

```bash
git commit -m "feat(rttp): exterior lane selection by commit-time route_probe cost"
```

---

### Task 4: `incremental_commit` hook

**Work classification:** implementation change

**Depends on:** Tasks 2–3

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/incremental_commit.py`
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py`
- Modify: `tests/unit/asteroid_lab/test_incremental_commit*.py` (or add `test_incremental_commit_exterior_lane.py`)

- [ ] **Step 1: Extend `CommitResult` / `incremental_commit` signature**

```python
@dataclass(frozen=True, slots=True)
class CommitResult:
    ...
    exterior_lane_assignments: tuple[dict[str, object], ...] = ()
    exterior_lane_assignment_state: tuple[ExteriorLaneAssignmentState, ...] = ()
```

Add optional parameter:

```python
def incremental_commit(
    ...,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None = None,
    resource_kind: str = "shape",  # for output_per_min rule lookup
) -> CommitResult:
```

When `exterior_lane_plan is None`, preserve current behavior (probe all `inp.route_goals`).

- [ ] **Step 2: Write failing integration test**

Commit two candidates with plan where second must spill to lane 1; assert `exterior_lane_assignments` records distinct `exterior_lane_id`.

- [ ] **Step 3: Hook `_attempt_commit_one`**

When plan present:
1. Resolve `candidate_throughput_per_min` via `get_active_rule(resource_kind)` + `output_per_min`.
2. Call `select_exterior_lane_for_candidate`.
3. On `None` → `CommitConflictReason.REPROBE_FAILED` (v0) + record diagnostic key `lane_capacity_shortfall` in assignment metrics dict (not free-form `failure_reason` on domain events).
4. On success → probe path to **selected** goal only (reuse returned `probe`); append assignment evidence.

- [ ] **Step 4: Wire pipeline**

```python
plan = build_exterior_lane_capacity_plan(...)
primary_commit_result = incremental_commit(
    ...,
    exterior_lane_plan=plan,
    resource_kind=resource_kind,
)
```

- [ ] **Step 5: Run narrow tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_assignment.py tests/unit/asteroid_lab/test_incremental_commit_exterior_lane.py -k incremental_commit -v`

- [ ] **Step 6: Commit (when user requests)**

```bash
git commit -m "feat(rttp): assign commits to exterior lanes with capacity limits"
```

---

### Task 5: Validation issue codes + read-only validator

**Work classification:** contract change

**Depends on:** Task 4

**Files:**
- Modify: `django_apps/asteroid_lab/contracts/rttp_layout_issue_codes.py`
- Create: `django_apps/asteroid_lab/optimization/validation/validate_exterior_lane_contract.py`
- Modify: `django_apps/asteroid_lab/optimization/validation/layout_connectivity_validation.py` or `validate_pipeline_layout`
- Create: `tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py`

- [ ] **Step 1: Add issue codes (with tests)**

```python
ISSUE_CODE_ROUTE_WITHOUT_LANE_ASSIGNMENT = "route_without_lane_assignment"
ISSUE_CODE_EXTERIOR_LANE_OVER_CAPACITY = "exterior_lane_over_capacity"
ISSUE_CODE_EXTERIOR_LANE_KIND_MISMATCH = "exterior_lane_kind_mismatch"
```

- [ ] **Step 2: Write failing validation tests**

Assert validator returns `exterior_lane_over_capacity` when mocked assignment exceeds capacity; assert **no mutation** of `reserved_route_cells`.

- [ ] **Step 3: Implement `validate_exterior_lane_contract`**

Inputs: `commit_result.exterior_lane_assignments`, `exterior_lane_plan`, `candidates_by_id`. Read-only.

- [ ] **Step 4: Integrate into `validate_pipeline_layout`**

Call when `exterior_lane_plan` was used for the run.

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py tests/unit/asteroid_lab/test_validation_readonly_guards.py -v`

- [ ] **Step 6: Commit (when user requests)**

```bash
git commit -m "feat(rttp): read-only exterior lane contract validation"
```

---

### Task 6: Metrics / replay output-only evidence

**Work classification:** implementation change

**Depends on:** Task 4

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py` (`rttp.commit` step metrics)

- [ ] **Step 1: Write failing test on pipeline metrics shape**

Assert `algorithm_steps` commit step includes:

```python
{
    "exterior_lane_plan": {
        "required_lane_count": 2,
        "lane_capacity_per_min": "2880",
        "max_asteroid_throughput_per_min": "5760",
    },
    "exterior_lane_assignments": [...],
    "external_lane_assigned_loads": {"exterior_lane:shape_belt:0": "480", ...},
}
```

- [ ] **Step 2: Emit metrics in `_record_pipeline_step` for commit phase**

Decimal fields as strings. Include diagnostics: `lane_capacity_shortfall_count`, `route_feasible_shortfall_count` when conflicts occur.

- [ ] **Step 3: Assert replay does not read metrics**

Extend or reference `test_persistence_does_not_read_replay_frames` pattern — document-only if already covered.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_rttp_pipeline_metrics.py -v` (create file if missing)

- [ ] **Step 5: Commit (when user requests)**

```bash
git commit -m "feat(rttp): emit exterior lane plan metrics on commit step"
```

---

### Task 7: Narrow regression + docs

**Work classification:** regression guard

**Depends on:** Tasks 1–6

- [ ] **Step 1: Run ELCP narrow gate**

```bash
python -m pytest tests/unit/asteroid_lab/test_exterior_lane_capacity_helpers.py tests/unit/asteroid_lab/test_exterior_lane_capacity_planner.py tests/unit/asteroid_lab/test_exterior_lane_assignment.py tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py tests/unit/asteroid_lab/test_required_external_connectors.py tests/unit/asteroid_lab/test_rttp_route_goals.py -v
python -m ruff check django_apps/asteroid_lab/contracts/exterior_lane_capacity.py django_apps/asteroid_lab/optimization/routing/exterior_lane_capacity_helpers.py django_apps/asteroid_lab/optimization/routing/exterior_lane_capacity_planner.py django_apps/asteroid_lab/optimization/commit/exterior_lane_assignment.py django_apps/asteroid_lab/optimization/validation/validate_exterior_lane_contract.py
python -m mypy django_apps/asteroid_lab/contracts/exterior_lane_capacity.py django_apps/asteroid_lab/optimization/routing/exterior_lane_capacity_helpers.py django_apps/asteroid_lab/optimization/routing/exterior_lane_capacity_planner.py django_apps/asteroid_lab/optimization/commit/exterior_lane_assignment.py
```

- [ ] **Step 2: Optional algorithm doc touch**

Add short cross-ref in `documents/Algorithm/asteroid_lab_01_optimization_input.md`: exterior lane plan + assignment state.

- [ ] **Step 3: Mark plan ACTIVE → CLOSED in `current_plan.md` when merged (post-PR)**

- [ ] **Step 4: Final commit (when user requests)**

```bash
git commit -m "test(rttp): ELCP regression gate and algorithm doc cross-ref"
```

---

## Spec coverage self-review

| Spec section | Task |
|--------------|------|
| §3 DTO split plan vs assignment state | Task 1 |
| §3 ELCP-N1 int count normalization | Task 1 |
| §3.4 plan construction | Task 2 |
| §4 nearest = route_probe, tie-break | Task 3–4 |
| §4.3 commit evidence JSON | Task 4, 6 |
| §5 validation read-only | Task 5 |
| §8 forbidden shortcuts | Tasks 3–6 (no Manhattan authority; no replay input) |
| §6 module map | File map above |

**Deferred (explicit):** ELCP-v1 weighted costs; EVTC-6b `route_not_shortest_feasible`; hard-fail `lane_capacity_shortfall` in validation.

---

## Subagent-driven execution notes

- **One implementer subagent per task** (Tasks 1–7); do not parallelize implementers (shared files).
- After each task: **spec compliance review** → **code quality review** (per superpowers:subagent-driven-development).
- Provide subagents: full task text + spec § excerpts + file map; do not point at plan file only.
- Use **fast model** for Task 1; **standard model** for Tasks 3–4 integration.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-30-rttp-exterior-lane-capacity-planner.md`.

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review between tasks.

**2. Inline Execution** — execute in this session via superpowers:executing-plans with checkpoints.

Which approach do you want to start Task 1 with?
