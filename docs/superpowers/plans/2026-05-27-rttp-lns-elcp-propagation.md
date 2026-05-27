# RTTP Local LNS — ELCP Context Propagation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the Run #238 wiring bug — `run_local_lns` must propagate ELCP context into retry `incremental_commit` calls and must not allow ELCP-incomplete retry results to replace ELCP-aware primary results.

**Architecture:** Add `elcp_commit_guard.py` with canonical `elcp_plan_is_active`, `is_elcp_incomplete_commit_result`, and `retry_may_replace_best`. Extend `run_local_lns` signature to mirror primary commit ELCP kwargs. Pipeline passes the same derived `resource_kind` and `route_probe_start_policy` as primary commit. All LNS return paths (including conflict-free early exit) use the guard when ELCP is active.

**Tech Stack:** Python 3.12+, Django 5.2, RTTP (`incremental_commit`, `run_local_lns`, `validate_exterior_lane_contract_issues`), pytest, ruff, mypy (`django_apps/asteroid_lab`).

**Canonical spec:** [`docs/superpowers/specs/2026-05-27-rttp-lns-elcp-propagation-design.md`](../specs/2026-05-27-rttp-lns-elcp-propagation-design.md)

**Work classification:** contract change · regression fix

---

## File map (create / modify)

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/optimization/commit/elcp_commit_guard.py` | **NEW** — ELCP active predicate, incomplete check, replacement gate |
| `django_apps/asteroid_lab/optimization/commit/local_lns.py` | ELCP kwargs, guard on all return paths, forward to `incremental_commit` |
| `django_apps/asteroid_lab/optimization/commit/__init__.py` | Export guard helpers if needed by tests |
| `django_apps/asteroid_lab/optimization/pipeline.py` | Pass ELCP context into `run_local_lns` |
| `tests/unit/asteroid_lab/test_elcp_commit_guard.py` | **NEW** — direct guard unit tests |
| `tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py` | **NEW** — LNS kwargs + replacement guard integration |
| `tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py` | Extend — validation bridge cardinality test |
| `tests/unit/asteroid_lab/test_rttp_lns.py` | Verify existing LNS tests still pass (non-ELCP path unchanged) |
| `documents/ai/current_plan.md` | ACTIVE row for LNS ELCP propagation |

---

## Normative reminders (from spec)

```text
When exterior_lane_plan is present in the primary RTTP commit path,
all repair/retry commit paths that may replace the primary CommitResult
must preserve ELCP context or must be disqualified from replacing an
ELCP-aware result.

All LNS return paths, including conflict-free early return, must pass
through retry_may_replace_best or an equivalent ELCP completeness guard
when ELCP is active.
```

---

### Task 1: Spec minor amendments (done)

**Files:**
- Modify: `docs/superpowers/specs/2026-05-27-rttp-lns-elcp-propagation-design.md`

- [x] **Step 1:** Apply reviewer amendments (canonical `required_lane_count`, guard module, early-exit MUST, exact propagation)
- [x] **Step 2:** Mark spec Approved; link this plan

No code changes in this task.

---

### Task 2: RED — `elcp_commit_guard` unit tests

**Work classification:** contract change (tests first)

**Files:**
- Create: `tests/unit/asteroid_lab/test_elcp_commit_guard.py`

- [ ] **Step 1: Write failing test file**

```python
"""ELCP commit guard — LNS replacement predicate (Run #238 regression)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ExteriorLaneCapacityPlan,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import RouteProbeStartPolicy
from django_apps.asteroid_lab.optimization.commit.elcp_commit_guard import (
    elcp_plan_is_active,
    is_elcp_incomplete_commit_result,
    retry_may_replace_best,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult
from django_apps.asteroid_lab.optimization.input_contracts import (
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)


def _goal(coord: tuple[int, int]) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=20,
        existing_trunk=False,
    )


def _plan(*, required_lane_count: int = 1) -> ExteriorLaneCapacityPlan:
    lanes = tuple(
        ExteriorTransportLane(
            lane_id=f"exterior_lane:shape_belt:{index}",
            transport_kind=TransportKind.SHAPE_BELT,
            connector_goal=_goal((5 + index, 5)),
            capacity_per_min=Decimal("2880"),
            target_load_per_min=Decimal("2880"),
            anchor_coord=(5 + index, 5),
        )
        for index in range(required_lane_count)
    )
    return ExteriorLaneCapacityPlan(
        transport_kind=TransportKind.SHAPE_BELT,
        max_asteroid_throughput_per_min=Decimal("5760"),
        lane_capacity_per_min=Decimal("2880"),
        required_lane_count=required_lane_count,
        lanes=lanes,
    )


def _commit_result(
    *,
    committed_ids: tuple[str, ...] = (),
    assignments: tuple[dict[str, object], ...] = (),
) -> CommitResult:
    return CommitResult(
        committed_ids=committed_ids,
        reserved_route_cells=frozenset(),
        domain_version=len(committed_ids),
        conflicts=(),
        exterior_lane_assignments=assignments,
    )


def test_elcp_plan_is_active_false_when_none() -> None:
    assert elcp_plan_is_active(None) is False


def test_elcp_plan_is_active_false_when_zero_lanes() -> None:
    assert elcp_plan_is_active(_plan(required_lane_count=0)) is False


def test_elcp_plan_is_active_true_when_required_lane_count_positive() -> None:
    assert elcp_plan_is_active(_plan(required_lane_count=2)) is True


def test_is_elcp_incomplete_false_when_plan_inactive() -> None:
    result = _commit_result(committed_ids=("a",), assignments=())
    assert is_elcp_incomplete_commit_result(exterior_lane_plan=None, commit_result=result) is False


def test_is_elcp_incomplete_false_when_no_commits() -> None:
    plan = _plan()
    result = _commit_result(committed_ids=(), assignments=())
    assert is_elcp_incomplete_commit_result(exterior_lane_plan=plan, commit_result=result) is False


def test_is_elcp_incomplete_false_when_cardinality_matches() -> None:
    plan = _plan()
    result = _commit_result(
        committed_ids=("a", "b"),
        assignments=(
            {"candidate_id": "a", "exterior_lane_id": "exterior_lane:shape_belt:0"},
            {"candidate_id": "b", "exterior_lane_id": "exterior_lane:shape_belt:0"},
        ),
    )
    assert is_elcp_incomplete_commit_result(exterior_lane_plan=plan, commit_result=result) is False


def test_is_elcp_incomplete_true_when_assignments_missing() -> None:
    plan = _plan()
    result = _commit_result(committed_ids=("a", "b"), assignments=())
    assert is_elcp_incomplete_commit_result(exterior_lane_plan=plan, commit_result=result) is True


def test_retry_may_replace_best_rejects_elcp_incomplete_higher_count() -> None:
    plan = _plan()
    primary = _commit_result(
        committed_ids=("keep",),
        assignments=(
            {"candidate_id": "keep", "exterior_lane_id": "exterior_lane:shape_belt:0"},
        ),
    )
    retry = _commit_result(
        committed_ids=("keep", "extra1", "extra2"),
        assignments=(),
    )
    assert retry_may_replace_best(
        exterior_lane_plan=plan,
        best_result=primary,
        retry_result=retry,
    ) is False


def test_retry_may_replace_best_accepts_elcp_complete_higher_count() -> None:
    plan = _plan()
    primary = _commit_result(
        committed_ids=("keep",),
        assignments=(
            {"candidate_id": "keep", "exterior_lane_id": "exterior_lane:shape_belt:0"},
        ),
    )
    retry = _commit_result(
        committed_ids=("keep", "extra"),
        assignments=(
            {"candidate_id": "keep", "exterior_lane_id": "exterior_lane:shape_belt:0"},
            {"candidate_id": "extra", "exterior_lane_id": "exterior_lane:shape_belt:0"},
        ),
    )
    assert retry_may_replace_best(
        exterior_lane_plan=plan,
        best_result=primary,
        retry_result=retry,
    ) is True


def test_retry_may_replace_best_unchanged_when_plan_inactive() -> None:
    primary = _commit_result(committed_ids=("a",))
    retry = _commit_result(committed_ids=("a", "b", "c"))
    assert retry_may_replace_best(
        exterior_lane_plan=None,
        best_result=primary,
        retry_result=retry,
    ) is True
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_elcp_commit_guard.py -v`  
Expected: `ModuleNotFoundError: elcp_commit_guard`

- [ ] **Step 3: Commit when user requests**

```bash
git add tests/unit/asteroid_lab/test_elcp_commit_guard.py
git commit -m "test(rttp): add RED tests for ELCP commit guard"
```

---

### Task 3: GREEN — `elcp_commit_guard.py`

**Files:**
- Create: `django_apps/asteroid_lab/optimization/commit/elcp_commit_guard.py`

- [ ] **Step 1: Implement guard module**

```python
"""Read-only ELCP commit completeness guards for LNS replacement."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import ExteriorLaneCapacityPlan
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult


def elcp_plan_is_active(exterior_lane_plan: ExteriorLaneCapacityPlan | None) -> bool:
    if exterior_lane_plan is None:
        return False
    return exterior_lane_plan.required_lane_count > 0


def is_elcp_incomplete_commit_result(
    *,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None,
    commit_result: CommitResult,
) -> bool:
    if not elcp_plan_is_active(exterior_lane_plan):
        return False
    if not commit_result.committed_ids:
        return False
    return len(commit_result.exterior_lane_assignments) != len(commit_result.committed_ids)


def retry_may_replace_best(
    *,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None,
    best_result: CommitResult,
    retry_result: CommitResult,
) -> bool:
    if len(retry_result.committed_ids) <= len(best_result.committed_ids):
        return False
    if is_elcp_incomplete_commit_result(
        exterior_lane_plan=exterior_lane_plan,
        commit_result=retry_result,
    ):
        return False
    return True


__all__ = [
    "elcp_plan_is_active",
    "is_elcp_incomplete_commit_result",
    "retry_may_replace_best",
]
```

- [ ] **Step 2: Run guard tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_elcp_commit_guard.py -v`  
Expected: all PASS

- [ ] **Step 3: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/optimization/commit/elcp_commit_guard.py tests/unit/asteroid_lab/test_elcp_commit_guard.py`

- [ ] **Step 4: Commit when user requests**

```bash
git add django_apps/asteroid_lab/optimization/commit/elcp_commit_guard.py tests/unit/asteroid_lab/test_elcp_commit_guard.py
git commit -m "feat(rttp): add ELCP commit guard helpers for LNS replacement"
```

---

### Task 4: RED — LNS retry kwargs propagation test

**Files:**
- Create: `tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py`

- [ ] **Step 1: Write failing propagation test**

Add to `test_rttp_lns_elcp_propagation.py`:

```python
"""LNS ELCP context propagation (Run #238 wiring regression)."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ExteriorLaneCapacityPlan,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import RouteProbeStartPolicy
from django_apps.asteroid_lab.optimization.commit import local_lns
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflict,
    CommitConflictReason,
    CommitResult,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome


def _goal(coord: tuple[int, int]) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=20,
        existing_trunk=False,
    )


def _plan() -> ExteriorLaneCapacityPlan:
    lane = ExteriorTransportLane(
        lane_id="exterior_lane:shape_belt:0",
        transport_kind=TransportKind.SHAPE_BELT,
        connector_goal=_goal((5, 5)),
        capacity_per_min=Decimal("2880"),
        target_load_per_min=Decimal("2880"),
        anchor_coord=(5, 5),
    )
    return ExteriorLaneCapacityPlan(
        transport_kind=TransportKind.SHAPE_BELT,
        max_asteroid_throughput_per_min=Decimal("2880"),
        lane_capacity_per_min=Decimal("2880"),
        required_lane_count=1,
        lanes=(lane,),
    )


def _candidate(candidate_id: str, *, anchor: tuple[int, int]) -> SimpleNamespace:
    return SimpleNamespace(
        candidate_id=candidate_id,
        anchor_coord=anchor,
        pattern=object(),
        occupied_cells=frozenset({anchor}),
        output_stub=(anchor[0], anchor[1] + 1),
        output_dir="N",
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=1,
        route_probe_cost=1,
        reachable=True,
    )


def test_local_lns_forwards_elcp_kwargs_to_incremental_commit(monkeypatch) -> None:
    plan = _plan()
    keep = _candidate("keep", anchor=(10, 10))
    conflicted = _candidate("conflict", anchor=(0, 0))
    candidates_by_id = {keep.candidate_id: keep, conflicted.candidate_id: conflicted}
    primary = CommitResult(
        committed_ids=(keep.candidate_id,),
        reserved_route_cells=frozenset(),
        domain_version=1,
        conflicts=(
            CommitConflict(
                candidate_id=conflicted.candidate_id,
                reason=CommitConflictReason.REPROBE_FAILED,
            ),
        ),
        exterior_lane_assignments=(
            {"candidate_id": keep.candidate_id, "exterior_lane_id": plan.lanes[0].lane_id},
        ),
    )
    captured: list[dict[str, object]] = []

    def _fake_incremental_commit(*_args, **kwargs):
        captured.append(dict(kwargs))
        return CommitResult(
            committed_ids=(keep.candidate_id,),
            reserved_route_cells=frozenset(),
            domain_version=1,
            conflicts=(),
            exterior_lane_assignments=(
                {"candidate_id": keep.candidate_id, "exterior_lane_id": plan.lanes[0].lane_id},
            ),
        )

    monkeypatch.setattr(local_lns, "generate_candidates", lambda *_a, **_k: SimpleNamespace(normal_candidates=()))
    monkeypatch.setattr(
        local_lns,
        "select_genome",
        lambda pool, *_a, **_k: PlacementGenome(
            commit_order=tuple(c.candidate_id for c in pool)
        ),
    )
    monkeypatch.setattr(local_lns, "initial_commit_domain", lambda *_a, **_k: object())
    monkeypatch.setattr(local_lns, "incremental_commit", _fake_incremental_commit)

    policy = RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED
    resource_kind = "shape"

    local_lns.run_local_lns(
        SimpleNamespace(),
        SimpleNamespace(),
        PlacementGenome(commit_order=(keep.candidate_id, conflicted.candidate_id)),
        candidates_by_id,
        primary,
        exterior_lane_plan=plan,
        route_probe_start_policy=policy,
        resource_kind=resource_kind,
    )

    assert captured, "incremental_commit should be invoked during LNS retry"
    for call_kwargs in captured:
        assert call_kwargs.get("exterior_lane_plan") is plan
        assert call_kwargs.get("route_probe_start_policy") is policy
        assert call_kwargs.get("resource_kind") == resource_kind
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py::test_local_lns_forwards_elcp_kwargs_to_incremental_commit -v`  
Expected: FAIL — `run_local_lns()` unexpected keyword argument `exterior_lane_plan` OR captured kwargs missing ELCP fields

---

### Task 5: RED — replacement guard integration test

**Files:**
- Modify: `tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py`

- [ ] **Step 1: Add failing guard integration test**

```python
def test_local_lns_rejects_elcp_incomplete_conflict_free_early_exit(monkeypatch) -> None:
    """Run #238 regression: higher commit count without assignments must not win."""
    plan = _plan()
    keep = _candidate("keep", anchor=(10, 10))
    conflicted = _candidate("conflict", anchor=(0, 0))
    candidates_by_id = {keep.candidate_id: keep, conflicted.candidate_id: conflicted}
    primary = CommitResult(
        committed_ids=(keep.candidate_id,),
        reserved_route_cells=frozenset(),
        domain_version=1,
        conflicts=(
            CommitConflict(
                candidate_id=conflicted.candidate_id,
                reason=CommitConflictReason.REPROBE_FAILED,
            ),
        ),
        exterior_lane_assignments=(
            {"candidate_id": keep.candidate_id, "exterior_lane_id": plan.lanes[0].lane_id},
        ),
    )

    monkeypatch.setattr(local_lns, "generate_candidates", lambda *_a, **_k: SimpleNamespace(normal_candidates=()))
    monkeypatch.setattr(
        local_lns,
        "select_genome",
        lambda pool, *_a, **_k: PlacementGenome(
            commit_order=tuple(c.candidate_id for c in pool)
        ),
    )
    monkeypatch.setattr(local_lns, "initial_commit_domain", lambda *_a, **_k: object())
    monkeypatch.setattr(
        local_lns,
        "incremental_commit",
        lambda *_a, **_k: CommitResult(
            committed_ids=(keep.candidate_id, "extra1", "extra2"),
            reserved_route_cells=frozenset(),
            domain_version=3,
            conflicts=(),
            exterior_lane_assignments=(),
        ),
    )

    _genome, final = local_lns.run_local_lns(
        SimpleNamespace(),
        SimpleNamespace(),
        PlacementGenome(commit_order=(keep.candidate_id, conflicted.candidate_id)),
        candidates_by_id,
        primary,
        exterior_lane_plan=plan,
        route_probe_start_policy=RouteProbeStartPolicy.OUTPUT_STUB_ONLY,
        resource_kind="shape",
    )

    assert final.committed_ids == primary.committed_ids
    assert final.exterior_lane_assignments == primary.exterior_lane_assignments
    assert _genome.commit_order == (keep.candidate_id, conflicted.candidate_id)
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py::test_local_lns_rejects_elcp_incomplete_conflict_free_early_exit -v`  
Expected: FAIL — final result has 3 commits with empty assignments

---

### Task 6: GREEN — `local_lns.py` signature + forwarding + guard

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/local_lns.py`

- [ ] **Step 1: Extend imports and signature**

Add imports:

```python
from django_apps.asteroid_lab.contracts.exterior_lane_capacity import ExteriorLaneCapacityPlan
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import RouteProbeStartPolicy
from django_apps.asteroid_lab.optimization.commit.elcp_commit_guard import retry_may_replace_best
```

Extend `run_local_lns` signature per spec §4.1 with `exterior_lane_plan`, `route_probe_start_policy`, `resource_kind`.

- [ ] **Step 2: Forward ELCP kwargs into `incremental_commit`**

Replace the retry call (lines ~114–120) with:

```python
        retry_result = incremental_commit(
            retry_genome,
            merged,
            inp,
            skeleton,
            domain=domain,
            route_probe_start_policy=route_probe_start_policy,
            exterior_lane_plan=exterior_lane_plan,
            resource_kind=resource_kind,
        )
```

- [ ] **Step 3: Apply guard on replacement and early exit**

Replace:

```python
        if len(retry_result.committed_ids) > len(best_result.committed_ids):
            best_genome = retry_genome
            best_result = retry_result
            candidates_by_id.clear()
            candidates_by_id.update(merged)

        if not retry_result.conflicts:
            candidates_by_id.clear()
            candidates_by_id.update(merged)
            return retry_genome, retry_result
```

With:

```python
        if retry_may_replace_best(
            exterior_lane_plan=exterior_lane_plan,
            best_result=best_result,
            retry_result=retry_result,
        ):
            best_genome = retry_genome
            best_result = retry_result
            candidates_by_id.clear()
            candidates_by_id.update(merged)

        if not retry_result.conflicts:
            if retry_may_replace_best(
                exterior_lane_plan=exterior_lane_plan,
                best_result=best_result,
                retry_result=retry_result,
            ):
                candidates_by_id.clear()
                candidates_by_id.update(merged)
                return retry_genome, retry_result
            continue
```

Note: early-exit path uses `continue` so conflict-free but ELCP-incomplete retry does not return; loop ends with `best_result` (primary or best ELCP-complete).

- [ ] **Step 4: Run LNS ELCP tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py tests/unit/asteroid_lab/test_rttp_lns.py -v`  
Expected: all PASS

- [ ] **Step 5: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/optimization/commit/local_lns.py tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py`

- [ ] **Step 6: Commit when user requests**

```bash
git add django_apps/asteroid_lab/optimization/commit/local_lns.py tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py
git commit -m "fix(rttp): propagate ELCP context through local LNS retries"
```

---

### Task 7: GREEN — `pipeline.py` call-site propagation

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py` (~lines 691–699)

- [ ] **Step 1: Pass ELCP context into `run_local_lns`**

```python
    if commit_result.conflicts:
        genome, commit_result = run_local_lns(
            inp,
            skeleton,
            genome,
            candidates_by_id,
            commit_result,
            policy=policy,
            exterior_lane_plan=exterior_lane_plan,
            route_probe_start_policy=route_probe_start_policy,
            resource_kind=_resource_kind_for_transport(inp.transport_kind),
        )
```

Use the **same** `exterior_lane_plan`, `route_probe_start_policy`, and `_resource_kind_for_transport(inp.transport_kind)` values already used for primary `incremental_commit` above in the same function.

- [ ] **Step 2: Run narrow pipeline-related tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py -v`  
Expected: PASS (shadow tests mock LNS; boundary test checks ordering)

- [ ] **Step 3: Commit when user requests**

```bash
git add django_apps/asteroid_lab/optimization/pipeline.py
git commit -m "fix(rttp): pass ELCP context from pipeline into run_local_lns"
```

---

### Task 8: RED/GREEN — validation bridge test

**Files:**
- Modify: `tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py`

- [ ] **Step 1: Add cardinality bridge test**

Reuse existing `_plan()`, `_shape_belt_candidate()` helpers in that file:

```python
def test_validate_exterior_lane_no_route_without_lane_when_assignments_match_commits() -> None:
    plan = _plan()
    candidate_id = "c0"
    snapshot = ExteriorLaneCommitValidationSnapshot(
        exterior_lane_assignments=(
            {
                "candidate_id": candidate_id,
                "exterior_lane_id": plan.lanes[0].lane_id,
            },
        ),
        exterior_lane_assignment_state=(
            ExteriorLaneAssignmentState(
                lane_id=plan.lanes[0].lane_id,
                assigned_load_per_min=Decimal("480"),
            ),
        ),
        exterior_lane_activations=(),
        exterior_lane_trunk_states=(),
        exterior_lane_route_evidence=(),
    )
    issues = validate_exterior_lane_contract_issues(
        committed_ids=(candidate_id,),
        lane_commit_snapshot=snapshot,
        candidates_by_id={candidate_id: _shape_belt_candidate(candidate_id)},
        exterior_lane_plan=plan,
    )
    assert ISSUE_CODE_ROUTE_WITHOUT_LANE_ASSIGNMENT not in issues
```

- [ ] **Step 2: Run test — expect PASS** (validation already correct; locks bridge)

Run: `python -m pytest tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py::test_validate_exterior_lane_no_route_without_lane_when_assignments_match_commits -v`

- [ ] **Step 3: Commit when user requests**

```bash
git add tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py
git commit -m "test(rttp): lock ELCP assignment cardinality validation bridge"
```

---

### Task 9: Narrow regression gate + Run #238 diagnostic

- [ ] **Step 1: Narrow pytest gate**

Run:

```bash
python -m pytest tests/unit/asteroid_lab/test_elcp_commit_guard.py tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py tests/unit/asteroid_lab/test_rttp_lns.py tests/unit/asteroid_lab/test_validate_exterior_lane_contract.py tests/unit/asteroid_lab/test_incremental_commit_elcp.py -v
```

Expected: all PASS

- [ ] **Step 2: Ruff + mypy (narrow)**

Run:

```bash
python -m ruff check django_apps/asteroid_lab/optimization/commit/elcp_commit_guard.py django_apps/asteroid_lab/optimization/commit/local_lns.py django_apps/asteroid_lab/optimization/pipeline.py tests/unit/asteroid_lab/test_elcp_commit_guard.py tests/unit/asteroid_lab/test_rttp_lns_elcp_propagation.py
python -m mypy django_apps/asteroid_lab/optimization/commit/elcp_commit_guard.py django_apps/asteroid_lab/optimization/commit/local_lns.py
```

Expected: clean

- [ ] **Step 3: Run #238 diagnostic re-extraction (optional manual)**

Re-run solver on `rttp-core-recovery-test-map` (`project_id=23`) and extract from latest `SolverRun.config_json.solver_summary`:

```python
# manage.py shell snippet
from django_apps.asteroid_lab.models import SolverRun
ss = (SolverRun.objects.filter(project_id=23).order_by("-id").first().config_json or {}).get("solver_summary") or {}
commit = next(s for s in ss.get("algorithm_steps") or [] if s.get("step_id") == "rttp.commit")
m = commit.get("metrics") or {}
print("committed", len(m.get("committed_ids") or []))
print("assignments", len(m.get("exterior_lane_assignments") or []))
print("layout_connectivity", m.get("layout_connectivity_issue_codes"))
print("issue_codes", ss.get("issue_codes"))
```

**Accept after fix:**

- `len(assignments) == len(committed_ids)` when committed > 0
- `route_without_lane_assignment` NOT emitted solely from empty assignments
- Throughput shortfall may still appear — acceptable

- [ ] **Step 4: Update `documents/ai/current_plan.md`**

Add ACTIVE row:

```markdown
**ACTIVE — LNS ELCP propagation** — Close Run #238 wiring bug (LNS retry ELCP context + replacement guard). Spec: [`2026-05-27-rttp-lns-elcp-propagation-design.md`](../docs/superpowers/specs/2026-05-27-rttp-lns-elcp-propagation-design.md). Plan: [`2026-05-27-rttp-lns-elcp-propagation.md`](../docs/superpowers/plans/2026-05-27-rttp-lns-elcp-propagation.md).
```

- [ ] **Step 5: Final commit when user requests**

```bash
git add documents/ai/current_plan.md
git commit -m "docs(rttp): mark LNS ELCP propagation plan active"
```

---

## Spec coverage self-review

| Spec requirement | Task |
|------------------|------|
| §3.1 repair-path parity | Tasks 6–7 |
| Strategy A — ELCP kwargs propagation | Tasks 4, 6–7 |
| Strategy B — replacement guard | Tasks 2–3, 5–6 |
| Early-exit guard MUST | Task 5–6 |
| Canonical `required_lane_count` predicate | Task 3 |
| Exact `resource_kind` / `route_probe_start_policy` propagation | Tasks 4, 6–7 |
| Validation bridge §3.4 | Task 8 |
| Non-ELCP unchanged | Task 9 (`test_rttp_lns.py`) |
| Out of scope items | Not in plan |

---

## Out of scope (unchanged)

- Primary ELCP reprobe failure 56/59
- `assign_fill_first_exterior_lane` policy changes
- Throughput tuning
- Timing instrumentation / `solver_summary_stack`
- Boundary JSONL RTTP stage emit
- 13D-SSR
- `deferred_retry_execute` ELCP (P1 follow-up)
- `incremental_commit_macro` ELCP (P1 follow-up)

---

## Post-merge follow-up queue

| Re-run outcome | Next queue |
|----------------|------------|
| Assignments populated + validation pass | Throughput / capacity tuning |
| Assignments populated + validation fail | ELCP route conflict detail |
| ELCP-aware LNS still low commits | Primary ELCP reprobe failure (P1) |
| Runtime still ~48s | `solver_summary_stack` timing |
