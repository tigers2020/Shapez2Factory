# RTTP Exterior Lane Trunk Merge (ELCP-TM) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When ELCP is enabled, exterior routes **fill lane 0 until capacity-saturated**, then activate the next lane; each active lane uses **one shared trunk** with **branch-only** new reservations so Lab maps no longer show one parallel belt per extractor.

**Architecture:** Keep static `ExteriorLaneCapacityPlan`. Add mutable-through-replacement `tuple[ExteriorLaneTrunkState, ...]` during `incremental_commit`. Replace `select_exterior_lane_for_candidate` (nearest-all-lanes) with `assign_fill_first_exterior_lane` + `partition_route_into_branch_and_trunk`. Pass `shareable_trunk_cells` into overlap checks; gate output spine extension at trunk attachment.

**Tech Stack:** Python 3.12+, Django 5.2, `Decimal`, RTTP (`incremental_commit`, `probe_route`, `RouteCellDomain`), `output_per_min` via game_data, pytest, ruff, mypy (`django_apps/asteroid_lab`).

**Canonical spec:** [`docs/superpowers/specs/2026-05-30-rttp-exterior-lane-trunk-merge-design.md`](../specs/2026-05-30-rttp-exterior-lane-trunk-merge-design.md)

**Parent:** [`docs/superpowers/specs/2026-05-30-rttp-exterior-lane-capacity-planner-design.md`](../specs/2026-05-30-rttp-exterior-lane-capacity-planner-design.md)

---

## File map (create / modify)

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/contracts/exterior_lane_capacity.py` | Add `ExteriorLaneTrunkState`, `ExteriorLaneRouteEvidence`, `ExteriorLaneActivationEvidence`, `ACTIVATION_REASON_CAPACITY_EXHAUSTED` |
| `django_apps/asteroid_lab/optimization/commit/exterior_lane_fill_first.py` | **NEW** — current fill lane, activation, probe goal set |
| `django_apps/asteroid_lab/optimization/commit/exterior_lane_trunk.py` | **NEW** — trunk state init/update, branch/trunk partition |
| `django_apps/asteroid_lab/optimization/commit/exterior_lane_assignment.py` | Wire TM selection result type; deprecate nearest-all-lanes export |
| `django_apps/asteroid_lab/optimization/commit/incremental_commit.py` | TM loop, `shareable_trunk_cells`, branch-only `committed_route_cells`, spine guard |
| `django_apps/asteroid_lab/contracts/rttp_layout_issue_codes.py` | TM issue codes |
| `django_apps/asteroid_lab/optimization/validation/validate_exterior_lane_contract.py` | TM read-only checks |
| `django_apps/asteroid_lab/optimization/pipeline.py` | Emit `exterior_lane_activations` / `exterior_lane_route_evidence` on commit step |
| `tests/unit/asteroid_lab/test_exterior_lane_fill_first.py` | **NEW** |
| `tests/unit/asteroid_lab/test_exterior_lane_trunk.py` | **NEW** |
| `tests/unit/asteroid_lab/test_exterior_lane_assignment.py` | Update nearest → fill-first expectations |
| `tests/unit/asteroid_lab/test_incremental_commit_elcp_tm.py` | **NEW** integration |
| `tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py` | TM validation cases |
| `documents/ai/current_plan.md` | ACTIVE ELCP-TM row |

---

### Task 0: Docs queue

**Files:**
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Add ACTIVE row**

```markdown
**ACTIVE — ELCP-TM** — Exterior lane trunk merge (fill-first + shared trunk). **NEXT: Task 1** DTOs. Spec: [`2026-05-30-rttp-exterior-lane-trunk-merge-design.md`](../specs/2026-05-30-rttp-exterior-lane-trunk-merge-design.md). Plan: [`2026-05-30-rttp-exterior-lane-trunk-merge.md`](2026-05-30-rttp-exterior-lane-trunk-merge.md). Depends on ELCP plan Tasks 1–7 (merged or on branch).
```

- [ ] **Step 2: Commit when user requests**

```bash
git add docs/superpowers/specs/2026-05-30-rttp-exterior-lane-trunk-merge-design.md docs/superpowers/plans/2026-05-30-rttp-exterior-lane-trunk-merge.md documents/ai/current_plan.md
git commit -m "docs(rttp): add ELCP-TM trunk merge spec and plan"
```

---

### Task 1: TM DTOs + activation reason constant

**Work classification:** contract change

**Files:**
- Modify: `django_apps/asteroid_lab/contracts/exterior_lane_capacity.py`
- Create: `tests/unit/asteroid_lab/test_exterior_lane_trunk_dtos.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/asteroid_lab/test_exterior_lane_trunk_dtos.py
from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    ExteriorLaneActivationEvidence,
    ExteriorLaneRouteEvidence,
    ExteriorLaneTrunkState,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def test_activation_reason_constant() -> None:
    assert ACTIVATION_REASON_CAPACITY_EXHAUSTED == "capacity_exhausted"


def test_trunk_state_frozen() -> None:
    row = ExteriorLaneTrunkState(
        lane_id="exterior_lane:shape_belt:0",
        transport_kind=TransportKind.SHAPE_BELT,
        active=True,
        assigned_load_per_min=Decimal("0"),
        trunk_cells=frozenset({(1, 2)}),
        connector_coord=(1, 5),
    )
    assert row.connector_coord == (1, 5)


def test_route_evidence_tuple_fields() -> None:
    ev = ExteriorLaneRouteEvidence(
        candidate_id="c0",
        lane_id="exterior_lane:shape_belt:0",
        candidate_throughput_per_min=Decimal("480"),
        branch_cells=((0, 1),),
        reused_trunk_cells=(),
        new_trunk_cells=((1, 1), (1, 2)),
        reached_connector_coord=(1, 5),
        reached_trunk_coord=None,
    )
    assert ev.branch_cells == ((0, 1),)
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_trunk_dtos.py -v`  
Expected: `ImportError` for `ExteriorLaneTrunkState`

- [ ] **Step 3: Implement DTOs**

Add to `exterior_lane_capacity.py`:

```python
ACTIVATION_REASON_CAPACITY_EXHAUSTED = "capacity_exhausted"

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
    activation_reason: str
```

- [ ] **Step 4: Run test — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_trunk_dtos.py -v`

- [ ] **Step 5: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/contracts/exterior_lane_capacity.py tests/unit/asteroid_lab/test_exterior_lane_trunk_dtos.py`

---

### Task 2: Trunk partition helpers

**Files:**
- Create: `django_apps/asteroid_lab/optimization/commit/exterior_lane_trunk.py`
- Create: `tests/unit/asteroid_lab/test_exterior_lane_trunk.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/asteroid_lab/test_exterior_lane_trunk.py
from django_apps.asteroid_lab.optimization.commit.exterior_lane_trunk import (
    initial_trunk_states,
    partition_path_branch_and_trunk,
    shareable_trunk_cells_from_states,
    update_trunk_state_after_commit,
)
from django_apps.asteroid_lab.contracts.exterior_lane_capacity import ExteriorLaneTrunkState
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from decimal import Decimal


def _state(trunk: frozenset[tuple[int, int]]) -> ExteriorLaneTrunkState:
    return ExteriorLaneTrunkState(
        lane_id="exterior_lane:shape_belt:0",
        transport_kind=TransportKind.SHAPE_BELT,
        active=True,
        assigned_load_per_min=Decimal("0"),
        trunk_cells=trunk,
        connector_coord=(3, 0),
    )


def test_partition_first_commit_establishes_trunk() -> None:
    path = ((0, 0), (1, 0), (2, 0), (3, 0))
    branch, reused, new_trunk = partition_path_branch_and_trunk(
        path=path,
        existing_trunk=frozenset(),
        connector_coord=(3, 0),
    )
    assert branch == ()
    assert reused == ()
    assert new_trunk == path


def test_partition_second_commit_reuses_trunk_with_branch_only() -> None:
    existing = frozenset({(1, 0), (2, 0), (3, 0)})
    path = ((0, 1), (0, 0), (1, 0), (2, 0))
    branch, reused, new_trunk = partition_path_branch_and_trunk(
        path=path,
        existing_trunk=existing,
        connector_coord=(3, 0),
    )
    assert branch == ((0, 1), (0, 0))
    assert reused == ((1, 0), (2, 0))
    assert new_trunk == ()


def test_shareable_trunk_union() -> None:
    s0 = _state(frozenset({(1, 0)}))
    s1 = ExteriorLaneTrunkState(
        lane_id="exterior_lane:shape_belt:1",
        transport_kind=TransportKind.SHAPE_BELT,
        active=True,
        assigned_load_per_min=Decimal("0"),
        trunk_cells=frozenset({(5, 0)}),
        connector_coord=(6, 0),
    )
    assert shareable_trunk_cells_from_states((s0, s1)) == frozenset({(1, 0), (5, 0)})
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_trunk.py -v`

- [ ] **Step 3: Implement `exterior_lane_trunk.py`**

```python
def initial_trunk_states(plan: ExteriorLaneCapacityPlan) -> tuple[ExteriorLaneTrunkState, ...]:
    return tuple(
        ExteriorLaneTrunkState(
            lane_id=lane.lane_id,
            transport_kind=lane.transport_kind,
            active=index == 0 and plan.required_lane_count > 0,
            assigned_load_per_min=Decimal("0"),
            trunk_cells=frozenset(),
            connector_coord=lane.connector_goal.coord,
        )
        for index, lane in enumerate(plan.lanes)
    )

def partition_path_branch_and_trunk(
    *,
    path: tuple[Coord, ...],
    existing_trunk: frozenset[Coord],
    connector_coord: Coord,
) -> tuple[tuple[Coord, ...], tuple[Coord, ...], tuple[Coord, ...]]:
    """Normative split (ELCP-TM §4.2):
    - reused = path cells already in existing_trunk (path order)
    - if existing_trunk empty: branch=(), new_trunk=path
    - else: branch = path prefix until first cell in existing_trunk (exclusive of reused cells)
            new_trunk = path cells not in existing_trunk AND not in branch
            (second commit: branch-only delta; new_trunk often ())
    """
    ...

def update_trunk_state_after_commit(
    state: ExteriorLaneTrunkState,
    *,
    new_trunk_cells: tuple[Coord, ...],
    assigned_delta: Decimal,
) -> ExteriorLaneTrunkState:
    return replace(
        state,
        trunk_cells=frozenset(state.trunk_cells | frozenset(new_trunk_cells)),
        assigned_load_per_min=state.assigned_load_per_min + assigned_delta,
    )
```

Implement `partition_path_branch_and_trunk` per spec §4.2: `branch_cells` = new cells before first `existing_trunk` hit; if no prior trunk, `new_trunk_cells` = full path cells (minus miner occupied handled upstream).

- [ ] **Step 4: Run — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_trunk.py -v`

- [ ] **Step 5: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/optimization/commit/exterior_lane_trunk.py tests/unit/asteroid_lab/test_exterior_lane_trunk.py`

---

### Task 3: Fill-first lane selection

**Files:**
- Create: `django_apps/asteroid_lab/optimization/commit/exterior_lane_fill_first.py`
- Create: `tests/unit/asteroid_lab/test_exterior_lane_fill_first.py`
- Modify: `tests/unit/asteroid_lab/test_exterior_lane_assignment.py` (replace nearest-lane tests)

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/asteroid_lab/test_exterior_lane_fill_first.py
from decimal import Decimal

from django_apps.asteroid_lab.optimization.commit.exterior_lane_fill_first import (
    FillFirstExteriorLaneResult,
    assign_fill_first_exterior_lane,
)
# Reuse _plan, _lane, _mini_domain, _candidate helpers from test_exterior_lane_assignment.py


def test_unreachable_lane0_with_capacity_does_not_pick_lane1(
    monkeypatch,
) -> None:
    """Lane0 has capacity but only lane1 is reachable -> failure, not lane1."""
    plan = _plan(
        _lane("exterior_lane:shape_belt:0", (0, 5)),
        _lane("exterior_lane:shape_belt:1", (0, 10)),
    )
    # Domain: traversable only toward (0,10), not (0,5)
    ...
    result = assign_fill_first_exterior_lane(...)
    assert result is None  # route_feasible_shortfall path


def test_lane0_saturated_activates_lane1(
    monkeypatch,
) -> None:
    plan = _plan(_lane("exterior_lane:shape_belt:0", (0, 5)), _lane("exterior_lane:shape_belt:1", (0, 10)))
    state = increment_assignment_state(
        initial_assignment_state(plan),
        lane_id="exterior_lane:shape_belt:0",
        delta=Decimal("2880"),
    )
    result = assign_fill_first_exterior_lane(
        ...,
        assignment_state=state,
        trunk_states=...,  # lane0 active saturated
        candidate_throughput_per_min=Decimal("480"),
    )
    assert result is not None
    assert result.lane_id == "exterior_lane:shape_belt:1"
    assert result.activation is not None
    assert result.activation.activation_reason == "capacity_exhausted"
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_fill_first.py -v`

- [ ] **Step 3: Implement `assign_fill_first_exterior_lane`**

```python
@dataclass(frozen=True, slots=True)
class FillFirstExteriorLaneResult:
    lane_id: str
    connector_coord: Coord
    route_probe_cost: int
    probe: RouteProbeResult
    activation: ExteriorLaneActivationEvidence | None
    reached_trunk_coord: Coord | None

def assign_fill_first_exterior_lane(
    candidate: BundleCandidate,
    *,
    plan: ExteriorLaneCapacityPlan,
    assignment_state: tuple[ExteriorLaneAssignmentState, ...],
    trunk_states: tuple[ExteriorLaneTrunkState, ...],
    domain: RouteCellDomain,
    candidate_throughput_per_min: Decimal,
    probe_start: Coord,
    max_expansions: int,
    trigger_candidate_id: str,
) -> FillFirstExteriorLaneResult | None:
    # Implement §3.2 from spec: current_lane by lowest non-saturated active index;
    # probe goals = trunk_cells | {connector}; on unreachable + capacity -> None;
    # on capacity exhausted -> activate next trunk_state.active=True, record activation evidence.
```

Use `probe_route` with `frozenset(goals)` and `goal_priority` from lane connector.

- [ ] **Step 4: Update `test_exterior_lane_assignment.py`**

Remove or rewrite tests that assert **closer lane1 wins over lane0 with capacity** — replace with fill-first imports or delete file content moved to `test_exterior_lane_fill_first.py`.

- [ ] **Step 5: Run all assignment tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_exterior_lane_fill_first.py tests/unit/asteroid_lab/test_exterior_lane_assignment.py -v`

---

### Task 4: Wire TM into `incremental_commit`

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/incremental_commit.py`
- Modify: `django_apps/asteroid_lab/optimization/commit/incremental_commit.py` — `CommitResult` fields
- Create: `tests/unit/asteroid_lab/test_incremental_commit_elcp_tm.py`

- [ ] **Step 1: Extend `CommitResult`**

```python
@dataclass(frozen=True, slots=True)
class CommitResult:
    ...
    exterior_lane_trunk_states: tuple[ExteriorLaneTrunkState, ...] = ()
    exterior_lane_route_evidence: tuple[ExteriorLaneRouteEvidence, ...] = ()
    exterior_lane_activations: tuple[ExteriorLaneActivationEvidence, ...] = ()
```

- [ ] **Step 2: Write failing integration test**

```python
# tests/unit/asteroid_lab/test_incremental_commit_elcp_tm.py
def test_two_miners_same_lane_share_trunk_cells(elcp_tm_fixture) -> None:
    result = incremental_commit(..., exterior_lane_plan=plan)
    assert len(result.committed_ids) == 2
    trunks = [s for s in result.exterior_lane_trunk_states if s.lane_id.endswith(":0")]
    assert len(trunks) == 1
    trunk0 = trunks[0]
    assert len(trunk0.trunk_cells) < len(result.reserved_route_cells)  # not 2x full paths
    evidences = result.exterior_lane_route_evidence
    assert evidences[1].reused_trunk_cells  # second miner reuses trunk
```

Build minimal fixture: 2 candidates, small grid domain, plan with `required_lane_count=1`, capacity large enough for both.

- [ ] **Step 3: Replace ELCP selection block**

In `incremental_commit` when `use_elcp`:

1. Initialize `trunk_states = initial_trunk_states(exterior_lane_plan)`.
2. Call `assign_fill_first_exterior_lane` instead of `select_exterior_lane_for_candidate`.
3. On success, `partition_path_branch_and_trunk` from `selection.probe.path`.
4. Pass `shareable_trunk_cells=shareable_trunk_cells_from_states(trunk_states)` into `_attempt_commit_one` (add parameter) and `_augment_route_cells_with_output_spine`.
5. `committed_route_cells |= frozenset(branch_cells) | frozenset(new_trunk_cells)` only.
6. Update `trunk_states` copy-on-write.

- [ ] **Step 4: TM output spine guard**

In `_augment_route_cells_with_output_spine`, add optional `stop_at_cells: frozenset[Coord] | None`; break outward loop when `nxt in stop_at_cells`.

- [ ] **Step 5: Run integration test**

Run: `python -m pytest tests/unit/asteroid_lab/test_incremental_commit_elcp_tm.py -v`

- [ ] **Step 6: Regression ELCP tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_incremental_commit_elcp.py tests/unit/asteroid_lab/test_exterior_lane_capacity_planner.py -v`

Update snapshots/assertions that assumed nearest-lane or full path union.

---

### Task 5: Issue codes + validation

**Files:**
- Modify: `django_apps/asteroid_lab/contracts/rttp_layout_issue_codes.py`
- Modify: `django_apps/asteroid_lab/optimization/validation/validate_exterior_lane_contract.py`
- Modify: `tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py`

- [ ] **Step 1: Add constants**

```python
ISSUE_CODE_EXTERIOR_LANE_PREMATURE_ACTIVATION = "exterior_lane_premature_activation"
ISSUE_CODE_EXTERIOR_LANE_TRUNK_NOT_SHARED = "exterior_lane_trunk_not_shared"
ISSUE_CODE_EXTERIOR_LANE_BRANCH_NOT_CONNECTED_TO_TRUNK = "exterior_lane_branch_not_connected_to_trunk"
```

- [ ] **Step 2: Failing validation test**

```python
def test_premature_activation_detected() -> None:
    commit_result = CommitResult(
        ...,
        exterior_lane_activations=(bad_activation,),
    )
    issues = validate_exterior_lane_contract_issues(...)
    assert ISSUE_CODE_EXTERIOR_LANE_PREMATURE_ACTIVATION in issues
```

- [ ] **Step 3: Implement validators** per spec §5.1 using activation evidence + route evidence.

- [ ] **Step 4: Run**

Run: `python -m pytest tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py -v`

---

### Task 6: Pipeline metrics

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py`

- [ ] **Step 1: Extend commit step metrics JSON** with `exterior_lane_activations` and `exterior_lane_route_evidence` (decimal strings, coord lists).

- [ ] **Step 2: Unit test** in `tests/unit/asteroid_lab/test_rttp_pipeline.py` or dedicated test if exists — assert keys present when plan enabled.

Run: `python -m pytest tests/unit/asteroid_lab/ -k "exterior_lane and pipeline" -v`

---

### Task 7: Narrow gate + plan close

- [ ] **Step 1: ELCP-TM narrow pytest**

Run:

```bash
python -m pytest tests/unit/asteroid_lab/test_exterior_lane_trunk_dtos.py tests/unit/asteroid_lab/test_exterior_lane_trunk.py tests/unit/asteroid_lab/test_exterior_lane_fill_first.py tests/unit/asteroid_lab/test_incremental_commit_elcp_tm.py tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py tests/unit/asteroid_lab/test_incremental_commit_elcp.py -v
```

- [ ] **Step 2: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/contracts/exterior_lane_capacity.py django_apps/asteroid_lab/optimization/commit/ django_apps/asteroid_lab/optimization/validation/validate_exterior_lane_contract.py`

- [ ] **Step 3: Mark plan item** in `current_plan.md` when merged (user-driven).

---

## Spec coverage self-review

| Spec § | Task |
|--------|------|
| §3 fill-first / activation guard | Task 3, 4 |
| §4 trunk / branch reservation | Task 2, 4 |
| §4.3 spine guard | Task 4 |
| §5.1 validation codes | Task 5 |
| §5.2 metrics | Task 6 |
| §5.4 feature gate | Task 4 (same `exterior_lane_plan` gate) |
| Capacity from resolver only | No change to planner; tests use fixtures |

## Placeholder scan

No TBD steps. Partition helper implementation note in Task 2 Step 3 is completed in implementation, not left vague in committed code.

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-30-rttp-exterior-lane-trunk-merge.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute in this session with checkpoints  

**Which approach do you want?**
