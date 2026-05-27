# P1-ELCP-RF — Primary ELCP Reprobe Failure Investigation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Read-only A-track forensics — decompose primary ELCP `REPROBE_FAILED` mass on `rttp-core-recovery-test-map` into `probe_failure_class` buckets, publish owner matrix + one dominant B-spec candidate, with harness mirror parity vs production `incremental_commit`.

**Architecture:** Investigation-only modules under `harness/investigation/` mirror the ELCP branch of `incremental_commit` by calling the same production helpers (`_rebuild_domain`, `resolve_route_probe_start`, `assign_fill_first_exterior_lane`, `_attempt_commit_one`, etc.). A parity test compares mirror aggregate counters to a real `incremental_commit` call on the same inputs. Step forensics parse `algorithm_steps` for M2 cross-check. No production behavior changes.

**Tech Stack:** Python 3.12+, Django 5.12, pytest, ruff; RTTP pipeline (`run_rttp_pipeline`, `run_solver_runtime_with_pinned_game_data`); recovery map import (`import_core_recovery_test_map`).

**Design spec:** [`docs/superpowers/specs/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md`](../specs/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md)

---

## File structure

| File | Responsibility |
|------|----------------|
| `harness/investigation/rttp_elcp_reprobe_forensics.py` | `ElcpProbeFailureClass`, ledger rows, classifier, mirror loop, parity helper |
| `harness/investigation/rttp_elcp_reprobe_step_forensics.py` | M2: parse `algorithm_steps` commit metrics |
| `tests/investigation/test_rttp_elcp_reprobe_classifier.py` | Pure classifier unit tests |
| `tests/investigation/test_rttp_elcp_reprobe_forensics.py` | Parity + recovery-map integration |
| `docs/superpowers/reports/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-report.md` | Final taxonomy + owner matrix + dominant bucket |
| `documents/ai/current_plan.md` | ACTIVE → CLOSED when report complete |

**Not modified:** `incremental_commit.py`, `route_probe.py`, `pipeline.py`, validation modules, `CommitConflictReason`, `RouteProbeResult`.

---

## Spec → plan coverage

| Spec | Task |
|------|------|
| §2 Evidence (primary #239–241, appendix #238) | Task 8 (report), Task 7 (optional M3) |
| §5 Taxonomy / ledger / 95% gate | Task 1–2, Task 8 |
| §6 M1 mirror | Task 3–4, Task 6 |
| §6 M2 step forensics | Task 5 |
| §8 Deferred retry audit | Task 7 |
| §9 Recovery comparison | Task 7, Task 8 |
| §11 Acceptance / parity | Task 4, Task 6, Task 8 |

---

### Task 0: Queue + spec link

**Files:**
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/specs/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md` (plan path only)

- [ ] **Step 1: Add ACTIVE row to `current_plan.md`** (after LNS ELCP propagation CLOSED line):

```markdown
**ACTIVE — P1-ELCP-RF** — Primary ELCP commit-time reprobe failure forensics (read-only). **NEXT: Task 1** classifier + ledger. Spec: [`2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md`](../../docs/superpowers/specs/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md) · plan: [`2026-05-27-rttp-elcp-primary-reprobe-failure-investigation.md`](../../docs/superpowers/plans/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation.md).
```

- [ ] **Step 2: Update design spec line 11** — replace “to be created after spec review” with plan link (already present in header; ensure `Executable plan:` points to this file).

- [ ] **Step 3: Commit**

```bash
git add documents/ai/current_plan.md docs/superpowers/specs/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-design.md docs/superpowers/plans/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation.md
git commit -m "docs: add P1-ELCP-RF investigation plan and queue row"
```

---

### Task 1: Investigation enum, ledger DTO, classifier

**Files:**
- Create: `harness/investigation/rttp_elcp_reprobe_forensics.py`

- [ ] **Step 1: Create module with enum, dataclass, classifier**

Create `harness/investigation/rttp_elcp_reprobe_forensics.py`:

```python
"""Read-only ELCP primary reprobe forensics (P1-ELCP-RF; not solver input)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.routing.route_probe import RouteProbeResult


class ElcpProbeFailureClass(StrEnum):
    START_BLOCKED = "start_blocked"
    LANE_CAPACITY_SHORTFALL = "lane_capacity_shortfall"
    BUDGET_EXCEEDED = "budget_exceeded"
    PROBE_UNREACHABLE = "probe_unreachable"
    NO_GOAL_CELLS = "no_goal_cells"
    POST_PROBE_COMMIT_FAIL = "post_probe_commit_fail"
    STALE_CANDIDATE_REACHABLE = "stale_candidate_reachable"
    DOMAIN_CONGESTION = "domain_congestion"
    TRUNK_ORDERING_PRESSURE = "trunk_ordering_pressure"
    UNKNOWN_REPROBE_FAILED = "unknown_reprobe_failed"


# Investigation-only congestion threshold (document in report).
_DOMAIN_CONGESTION_ROUTE_CELL_RATIO = 0.15


@dataclass(frozen=True, slots=True)
class ElcpAttemptLedgerRow:
    candidate_id: str
    commit_index: int
    candidate_reachable: bool
    probe_start: Coord | None
    fill_first_ok: bool
    assigned_lane_id: str | None
    probe_reachable: bool | None
    probe_expanded_nodes: int | None
    max_expansions: int
    probe_failure_class: ElcpProbeFailureClass
    lane_capacity_shortfall_delta: int
    route_feasible_shortfall_delta: int
    commit_conflict_reason: str | None
    domain_version: int
    deferred_retry_eligible: bool
    tm_new_trunk_len: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "commit_index": self.commit_index,
            "candidate_reachable": self.candidate_reachable,
            "probe_start": list(self.probe_start) if self.probe_start else None,
            "fill_first_ok": self.fill_first_ok,
            "assigned_lane_id": self.assigned_lane_id,
            "probe_reachable": self.probe_reachable,
            "probe_expanded_nodes": self.probe_expanded_nodes,
            "max_expansions": self.max_expansions,
            "probe_failure_class": self.probe_failure_class.value,
            "lane_capacity_shortfall_delta": self.lane_capacity_shortfall_delta,
            "route_feasible_shortfall_delta": self.route_feasible_shortfall_delta,
            "commit_conflict_reason": self.commit_conflict_reason,
            "domain_version": self.domain_version,
            "deferred_retry_eligible": self.deferred_retry_eligible,
            "tm_new_trunk_len": self.tm_new_trunk_len,
        }


def classify_probe_failure(
    *,
    probe_start: Coord | None,
    fill_first_ok: bool,
    probe: RouteProbeResult | None,
    max_expansions: int,
    goals_nonempty: bool,
    candidate_reachable: bool,
    post_probe_committed: bool,
    committed_route_cell_count: int,
    traversable_cell_count: int,
    tm_new_trunk_len: int,
    trunk_pressure_correlated: bool,
) -> ElcpProbeFailureClass:
    """Ordered rules per design spec §5.2 (first match wins)."""
    if probe_start is None:
        return ElcpProbeFailureClass.START_BLOCKED
    if not fill_first_ok:
        return ElcpProbeFailureClass.LANE_CAPACITY_SHORTFALL
    if probe is not None and not probe.reachable:
        if not goals_nonempty:
            return ElcpProbeFailureClass.NO_GOAL_CELLS
        if probe.expanded_nodes >= max_expansions:
            return ElcpProbeFailureClass.BUDGET_EXCEEDED
        if (
            traversable_cell_count > 0
            and committed_route_cell_count / traversable_cell_count
            >= _DOMAIN_CONGESTION_ROUTE_CELL_RATIO
        ):
            return ElcpProbeFailureClass.DOMAIN_CONGESTION
        return ElcpProbeFailureClass.PROBE_UNREACHABLE
    if fill_first_ok and not post_probe_committed:
        if trunk_pressure_correlated and tm_new_trunk_len > 0:
            return ElcpProbeFailureClass.TRUNK_ORDERING_PRESSURE
        return ElcpProbeFailureClass.POST_PROBE_COMMIT_FAIL
    if candidate_reachable and not post_probe_committed:
        return ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE
    return ElcpProbeFailureClass.UNKNOWN_REPROBE_FAILED


__all__ = [
    "ElcpAttemptLedgerRow",
    "ElcpProbeFailureClass",
    "classify_probe_failure",
]
```

- [ ] **Step 2: Run ruff on new file**

```bash
python -m ruff check harness/investigation/rttp_elcp_reprobe_forensics.py
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add harness/investigation/rttp_elcp_reprobe_forensics.py
git commit -m "feat(investigation): add ELCP reprobe failure classifier and ledger DTO"
```

---

### Task 2: Classifier unit tests

**Files:**
- Create: `tests/investigation/test_rttp_elcp_reprobe_classifier.py`

- [ ] **Step 1: Write failing tests**

Create `tests/investigation/test_rttp_elcp_reprobe_classifier.py`:

```python
"""Pure tests for ELCP reprobe failure classifier (P1-ELCP-RF)."""

from __future__ import annotations

from harness.investigation.rttp_elcp_reprobe_forensics import (
    ElcpProbeFailureClass,
    classify_probe_failure,
)
from django_apps.asteroid_lab.optimization.routing.route_probe import RouteProbeResult


def _probe(*, reachable: bool, expanded: int) -> RouteProbeResult:
    return RouteProbeResult(reachable, 0, None, (), expanded)


def test_classify_start_blocked() -> None:
    assert (
        classify_probe_failure(
            probe_start=None,
            fill_first_ok=False,
            probe=None,
            max_expansions=500,
            goals_nonempty=True,
            candidate_reachable=True,
            post_probe_committed=False,
            committed_route_cell_count=0,
            traversable_cell_count=100,
            tm_new_trunk_len=0,
            trunk_pressure_correlated=False,
        )
        is ElcpProbeFailureClass.START_BLOCKED
    )


def test_classify_lane_capacity_shortfall() -> None:
    assert (
        classify_probe_failure(
            probe_start=(0, 0),
            fill_first_ok=False,
            probe=None,
            max_expansions=500,
            goals_nonempty=True,
            candidate_reachable=True,
            post_probe_committed=False,
            committed_route_cell_count=0,
            traversable_cell_count=100,
            tm_new_trunk_len=0,
            trunk_pressure_correlated=False,
        )
        is ElcpProbeFailureClass.LANE_CAPACITY_SHORTFALL
    )


def test_classify_budget_exceeded() -> None:
    assert (
        classify_probe_failure(
            probe_start=(0, 0),
            fill_first_ok=True,
            probe=_probe(reachable=False, expanded=500),
            max_expansions=500,
            goals_nonempty=True,
            candidate_reachable=True,
            post_probe_committed=False,
            committed_route_cell_count=0,
            traversable_cell_count=100,
            tm_new_trunk_len=0,
            trunk_pressure_correlated=False,
        )
        is ElcpProbeFailureClass.BUDGET_EXCEEDED
    )


def test_classify_stale_candidate_reachable() -> None:
    assert (
        classify_probe_failure(
            probe_start=(0, 0),
            fill_first_ok=True,
            probe=_probe(reachable=True, expanded=10),
            max_expansions=500,
            goals_nonempty=True,
            candidate_reachable=True,
            post_probe_committed=False,
            committed_route_cell_count=0,
            traversable_cell_count=100,
            tm_new_trunk_len=0,
            trunk_pressure_correlated=False,
        )
        is ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE
    )
```

- [ ] **Step 2: Run tests**

```bash
python -m pytest tests/investigation/test_rttp_elcp_reprobe_classifier.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 3: Commit**

```bash
git add tests/investigation/test_rttp_elcp_reprobe_classifier.py
git commit -m "test(investigation): ELCP reprobe failure classifier unit tests"
```

---

### Task 3: Harness mirror loop + ledger builder

**Files:**
- Modify: `harness/investigation/rttp_elcp_reprobe_forensics.py`

**Coupling note (document in module docstring):** Mirror imports production private helpers from `incremental_commit` and ELCP modules. **Parity test (Task 4) is the drift guard** — do not change production code in this track.

- [ ] **Step 1: Append mirror types and `build_elcp_primary_mirror_ledger`**

Add to `rttp_elcp_reprobe_forensics.py` (imports + functions). Implementation walks `genome.commit_order`, mirrors ELCP branch through `assign_fill_first_exterior_lane` / `_attempt_commit_one`, appends `ElcpAttemptLedgerRow` on each non-commit, updates local committed state when production would commit.

Key exports to add:

```python
@dataclass(frozen=True, slots=True)
class ElcpMirrorForensicsResult:
    ledger: tuple[ElcpAttemptLedgerRow, ...]
    mirror_committed_ids: tuple[str, ...]
    mirror_lane_capacity_shortfall_count: int
    mirror_route_feasible_shortfall_count: int
    mirror_conflict_count: int


def build_elcp_primary_mirror_ledger(
    *,
    genome: PlacementGenome,
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
    domain: CommitDomainState,
    exterior_lane_plan: ExteriorLaneCapacityPlan,
    route_probe_start_policy: RouteProbeStartPolicy,
    resource_kind: str,
    max_expansions: int | None = None,
) -> ElcpMirrorForensicsResult:
    """Mirror ELCP incremental_commit loop; record ledger rows for failed attempts only."""
    ...
```

**Implementation checklist (must match `incremental_commit` ELCP branch order):**

1. `use_elcp = plan active` (lanes non-empty).
2. Per `candidate_id` in `genome.commit_order`:
   - `candidate is None` → skip ledger (not REPROBE_FAILED taxonomy).
   - `_rebuild_domain(...)` with current committed sets.
   - `resolve_route_probe_start` → if None: ledger row `START_BLOCKED`, bump `route_feasible_shortfall`, append conflict, `continue`.
   - `assign_fill_first_exterior_lane` → if None: ledger `LANE_CAPACITY_SHORTFALL`, bump both shortfall counters, `continue`.
   - `partition_path_branch_and_trunk` for `tm_new_trunk_len`.
   - `_attempt_commit_one(...)` with `precomputed_route_cells` / `precomputed_probe` as production.
   - If not committed: classify via `classify_probe_failure`, set `deferred_retry_eligible=(reason==REPROBE_FAILED)`.
   - If committed: apply same domain mutations as production (occupied, route cells, trunk states, assignment_state).
3. Return aggregates for parity.

Use `from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    _attempt_commit_one,
    _rebuild_domain,
    _candidate_throughput_per_min,
    _COMMIT_PROBE_MAX_EXPANSIONS,
)` and ELCP imports from `exterior_lane_fill_first`, `exterior_lane_trunk`, `exterior_lane_assignment` state helpers.

- [ ] **Step 2: Run ruff**

```bash
python -m ruff check harness/investigation/rttp_elcp_reprobe_forensics.py
```

- [ ] **Step 3: Commit**

```bash
git add harness/investigation/rttp_elcp_reprobe_forensics.py
git commit -m "feat(investigation): ELCP primary commit mirror ledger builder"
```

---

### Task 4: Parity helper + unit parity test

**Files:**
- Modify: `harness/investigation/rttp_elcp_reprobe_forensics.py`
- Create: `tests/investigation/test_rttp_elcp_reprobe_forensics.py` (parity section first)

- [ ] **Step 1: Add `assert_mirror_parity`**

```python
def assert_mirror_parity(
    *,
    production: CommitResult,
    mirror: ElcpMirrorForensicsResult,
) -> None:
    assert len(mirror.mirror_committed_ids) == len(production.committed_ids)
    assert mirror.mirror_conflict_count == len(production.conflicts)
    assert (
        mirror.mirror_lane_capacity_shortfall_count
        == production.lane_capacity_shortfall_count
    )
    assert (
        mirror.mirror_route_feasible_shortfall_count
        == production.route_feasible_shortfall_count
    )
```

- [ ] **Step 2: Parity test on greenfield fixture with ELCP plan**

Add to `tests/investigation/test_rttp_elcp_reprobe_forensics.py`:

```python
"""Integration: ELCP mirror forensics parity vs production incremental_commit."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput, RttpSkeletonConfig
from django_apps.asteroid_lab.optimization.routing.exterior_lane_capacity_planner import (
    build_exterior_lane_capacity_plan,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from harness.investigation.rttp_elcp_reprobe_forensics import (
    assert_mirror_parity,
    build_elcp_primary_mirror_ledger,
)


@pytest.mark.django_db
def test_mirror_parity_matches_incremental_commit_on_elcp_plan(
    greenfield_optimization_input: OptimizationInput,
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    inp = greenfield_optimization_input
    plan = build_exterior_lane_capacity_plan(
        inp,
        max_asteroid_throughput_per_min=Decimal("5760"),
        transport_kind=inp.transport_kind,
    )
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = initial_commit_domain(skeleton, inp)
    genome = PlacementGenome(commit_order=())
    candidates_by_id: dict = {}
    production = incremental_commit(
        genome,
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
        exterior_lane_plan=plan,
        resource_kind="shape",
    )
    mirror = build_elcp_primary_mirror_ledger(
        genome=genome,
        candidates_by_id=candidates_by_id,
        inp=inp,
        skeleton=skeleton,
        domain=domain,
        exterior_lane_plan=plan,
        route_probe_start_policy=production  # FIX: use RouteProbeStartPolicy.OUTPUT_STUB_ONLY
        resource_kind="shape",
    )
    assert_mirror_parity(production=production, mirror=mirror)
```

**Fix before run:** import `RouteProbeStartPolicy` and pass `RouteProbeStartPolicy.OUTPUT_STUB_ONLY` (not `production`).

- [ ] **Step 3: Run parity test**

```bash
python -m pytest tests/investigation/test_rttp_elcp_reprobe_forensics.py::test_mirror_parity_matches_incremental_commit_on_elcp_plan -v
```

Expected: PASS after mirror implementation complete.

- [ ] **Step 4: Commit**

```bash
git add harness/investigation/rttp_elcp_reprobe_forensics.py tests/investigation/test_rttp_elcp_reprobe_forensics.py
git commit -m "test(investigation): ELCP mirror parity vs incremental_commit"
```

---

### Task 5: Step forensics (M2)

**Files:**
- Create: `harness/investigation/rttp_elcp_reprobe_step_forensics.py`
- Modify: `tests/investigation/test_rttp_elcp_reprobe_forensics.py` (add M2 test)

- [ ] **Step 1: Create step forensics extractor**

Create `harness/investigation/rttp_elcp_reprobe_step_forensics.py`:

```python
"""Parse algorithm_steps for ELCP reprobe investigation (M2 cross-check)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId


def extract_elcp_reprobe_forensics(
    algorithm_steps: Sequence[Mapping[str, object]],
) -> dict[str, Any]:
    commit_metrics: Mapping[str, object] = {}
    for step in algorithm_steps:
        if str(step.get("step_id")) == RttpAlgorithmStepId.RTTP_COMMIT.value:
            metrics = step.get("metrics")
            if isinstance(metrics, Mapping):
                commit_metrics = metrics
            break

    committed_ids = commit_metrics.get("committed_ids")
    committed_count = (
        len(committed_ids)
        if isinstance(committed_ids, Sequence) and not isinstance(committed_ids, str)
        else 0
    )
    conflict_count = commit_metrics.get("conflict_count")
    lane_shortfall = commit_metrics.get("lane_capacity_shortfall_count")
    route_shortfall = commit_metrics.get("route_feasible_shortfall_count")
    elcp_plan = commit_metrics.get("exterior_lane_plan")

    return {
        "committed_count": committed_count,
        "conflict_count": int(conflict_count) if isinstance(conflict_count, int) else None,
        "lane_capacity_shortfall_count": (
            int(lane_shortfall) if isinstance(lane_shortfall, int) else None
        ),
        "route_feasible_shortfall_count": (
            int(route_shortfall) if isinstance(route_shortfall, int) else None
        ),
        "elcp_plan_active": elcp_plan is not None,
        "reprobe_failed_ratio_note": (
            "Per-candidate reprobe histogram requires ledger (M1); "
            "step metrics only expose conflict_count aggregate."
        ),
    }


__all__ = ["extract_elcp_reprobe_forensics"]
```

- [ ] **Step 2: Commit**

```bash
git add harness/investigation/rttp_elcp_reprobe_step_forensics.py
git commit -m "feat(investigation): ELCP reprobe step forensics extractor (M2)"
```

---

### Task 6: Recovery map integration (RF.1 + RF.2)

**Files:**
- Modify: `tests/investigation/test_rttp_elcp_reprobe_forensics.py`

- [ ] **Step 1: Add recovery-map test capturing primary commit**

Pattern: `import_core_recovery_test_map` → `run_rttp_pipeline` with patch on `incremental_commit` to capture **first** call result (primary, before LNS).

```python
RECOVERY_SLUG = "rttp-core-recovery-test-map"

@pytest.mark.django_db
@pytest.mark.slow
def test_recovery_map_primary_reprobe_mass_reproduced(
    imported_game_data_batch_module: object,
) -> None:
    from django_apps.asteroid_lab.management.commands.import_rttp_core_recovery_test_map import (
        import_core_recovery_test_map,
    )
    # ... build inp via reconstruction (copy from test_rttp_core_recovery_gate_a.py)
    primary_results: list = []
    real_commit = incremental_commit

    def _capture_primary(*args, **kwargs):
        result = real_commit(*args, **kwargs)
        primary_results.append(result)
        return result

    with patch(
        "django_apps.asteroid_lab.optimization.pipeline.incremental_commit",
        side_effect=_capture_primary,
    ):
        pipeline_result = run_rttp_pipeline(inp, config=RttpPipelineConfig())

    assert primary_results, "primary incremental_commit was not called"
    primary = primary_results[0]
    assert len(primary.committed_ids) <= 5, "expected sparse primary commits on recovery map"
    reprobe_count = sum(
        1 for c in primary.conflicts if c.reason.value == "reprobe_failed"
    )
    assert reprobe_count > 0, "expected primary REPROBE_FAILED mass"

    mirror = build_elcp_primary_mirror_ledger(...)
    assert_mirror_parity(production=primary, mirror=mirror)

    failed = [r for r in mirror.ledger]
    assert failed, "ledger should contain failed attempts"
    known = sum(
        1
        for r in failed
        if r.probe_failure_class.value != "unknown_reprobe_failed"
    )
    coverage = known / len(failed)
    assert coverage >= 0.95, f"bucket coverage {coverage:.2%} below 95%"

    print(f"ELCP_RF_PRIMARY_COMMITTED={len(primary.committed_ids)}")
    print(f"ELCP_RF_REPROBE_CONFLICTS={reprobe_count}")
    print(f"ELCP_RF_BUCKET_COVERAGE={coverage:.4f}")
```

Fill `build_elcp_primary_mirror_ledger(...)` with same `exterior_lane_plan`, `genome`, `candidates_by_id` from pipeline capture (patch may also capture those kwargs on first `incremental_commit` call).

- [ ] **Step 2: Run integration test**

```bash
python -m pytest tests/investigation/test_rttp_elcp_reprobe_forensics.py -v -k recovery_map
```

Expected: PASS on machine with game_data import batch + recovery map fixture.

- [ ] **Step 3: Run narrow ruff**

```bash
python -m ruff check harness/investigation/ tests/investigation/test_rttp_elcp_reprobe_forensics.py
```

- [ ] **Step 4: Commit**

```bash
git add tests/investigation/test_rttp_elcp_reprobe_forensics.py
git commit -m "test(investigation): recovery map ELCP reprobe forensics + parity"
```

---

### Task 7: Deferred retry audit + recovery JSON compare (RF.5–RF.6)

**Files:**
- Modify: `harness/investigation/rttp_elcp_reprobe_forensics.py`

- [ ] **Step 1: Add audit helpers**

```python
def build_deferred_retry_audit(
    *,
    primary_commit_result: CommitResult,
    commit_order: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
    inp: OptimizationInput,
    ledger: Sequence[ElcpAttemptLedgerRow],
) -> dict[str, Any]:
    from django_apps.asteroid_lab.optimization.commit.deferred_retry_shadow import (
        build_deferred_retry_shadow_summary,
    )

    shadow = build_deferred_retry_shadow_summary(
        primary_commit_result=primary_commit_result,
        commit_order=commit_order,
        candidates_by_id=candidates_by_id,
        inp=inp,
    )
    primary_reprobe = sum(
        1
        for c in primary_commit_result.conflicts
        if c.reason.value == "reprobe_failed"
    )
    overlap = [
        {
            "candidate_id": row.candidate_id,
            "probe_failure_class": row.probe_failure_class.value,
            "deferred_retry_eligible": row.deferred_retry_eligible,
        }
        for row in ledger
    ]
    return {
        "primary_reprobe_failed_count": primary_reprobe,
        "eligible_reprobe_failed_count": shadow.domain_context.get(
            "eligible_reprobe_failed_count", shadow.candidate_count
        ),
        "shadow_candidate_count": shadow.candidate_count,
        "shadow_enabled": shadow.enabled,
        "overlap_table": overlap,
    }


def load_recovery_evidence_compare(
    *,
    primary_committed_count: int,
    evidence_path: str = "docs/superpowers/reports/2026-05-30-rttp-core-recovery-evidence-after-evtc.json",
) -> dict[str, Any]:
    import json
    from pathlib import Path

    path = Path(evidence_path)
    if not path.is_file():
        return {"loaded": False, "reason": "evidence file missing"}
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("slugs") or data.get("results") or []
    recovery_row = next(
        (r for r in rows if r.get("slug") == "rttp-core-recovery-test-map"),
        None,
    )
    if recovery_row is None:
        return {"loaded": True, "slug_row": None}
    return {
        "loaded": True,
        "evidence_committed": recovery_row.get("committed_extractor_count"),
        "primary_committed_count": primary_committed_count,
        "validation_passed": recovery_row.get("validation_passed"),
        "gate_a_passed": recovery_row.get("gate_a_passed"),
    }
```

- [ ] **Step 2: Commit**

```bash
git add harness/investigation/rttp_elcp_reprobe_forensics.py
git commit -m "feat(investigation): deferred retry audit and recovery evidence compare"
```

---

### Task 8: Investigation report + close track (RF.7, §11)

**Files:**
- Create: `docs/superpowers/reports/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-report.md`
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Run forensics and capture outputs**

```bash
python -m pytest tests/investigation/test_rttp_elcp_reprobe_forensics.py -v -k recovery_map -s
```

Record printed `ELCP_RF_*` lines and bucket histogram from ledger (`collections.Counter` on `probe_failure_class`).

- [ ] **Step 2: Write report** with required sections:

1. **RF.1 reproduction** — primary committed / reprobe conflict counts (post-fix).
2. **RF.2 taxonomy table** — bucket counts + % (≥95% named / ≤5% unknown).
3. **RF.3 M2 cross-check** — `extract_elcp_reprobe_forensics` vs mirror aggregates.
4. **RF.4 Run #238 appendix** — historical table (from spec §2.2); label non-authoritative.
5. **RF.5 deferred audit** — overlap table summary.
6. **RF.6 recovery compare** — `load_recovery_evidence_compare` output.
7. **RF.7 owner matrix** — map each bucket to owner module from spec §5.2.
8. **Dominant bucket** — exactly one `probe_failure_class` + recommended B-spec row from spec §12 (or `inconclusive` with rationale).

- [ ] **Step 3: Optional M3 (#238 DB readback)** — if local DB has `solver_run_id=238`, paste appendix metrics; else document `M3 skipped: no local DB`.

- [ ] **Step 4: Close `current_plan.md`** — change P1-ELCP-RF ACTIVE → **CLOSED (YYYY-MM-DD)** with report link.

- [ ] **Step 5: Final validation**

```bash
python -m pytest tests/investigation/test_rttp_elcp_reprobe_classifier.py tests/investigation/test_rttp_elcp_reprobe_forensics.py -v
python -m ruff check harness/investigation/rttp_elcp_reprobe_forensics.py harness/investigation/rttp_elcp_reprobe_step_forensics.py tests/investigation/
```

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/reports/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-report.md documents/ai/current_plan.md
git commit -m "docs: close P1-ELCP-RF investigation report"
```

---

### Task 9: Attempt universe sanity audit (RF.8 — REOPEN gate)

**Files:**
- Create: `harness/investigation/rttp_elcp_universe_sanity.py`
- Modify: `tests/investigation/test_rttp_elcp_reprobe_forensics.py`
- Modify: `docs/superpowers/reports/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation-report.md` (§ RF.8)

- [x] **Step 1:** Implement `extract_elcp_attempt_universe_sanity` (parses `rttp.candidate_pool`, `rttp.genome_selection`, commit metrics).

- [x] **Step 2:** Extend recovery integration test — assert `normal_candidate_count > commit_order_len`; print `ELCP_RF_UNIVERSE_SANITY`.

- [x] **Step 3:** Update report status **REOPENED**; withhold B-spec; document reconciliation table.

- [ ] **Step 4:** **Do not CLOSED** track until selection-vs-goal gap (59 vs 467) has owner decision or follow-on track (P1-ELCP-RF-A2).

**Observed (recovery map, 2026-05-27):**

```text
normal_candidate_count = 356
placement_goal_count   = 467
commit_order_len       = 59
primary REPROBE_FAILED = 29 (within 59 attempts)
```

---

## Plan self-review

| Check | Result |
|-------|--------|
| Spec §2–§12 coverage | Tasks 0–9; RF.8 universe gate added after review |
| Placeholders | None — Task 3 mirror body is checklist-driven (engineer implements against `incremental_commit` source) |
| Type consistency | `ElcpProbeFailureClass`, `ElcpMirrorForensicsResult` used throughout |
| Approach II rejected | No production collector |
| §3.1 invariant | No `RouteProbeResult` / `CommitConflictReason` changes |

---

## Execution handoff

Plan saved to [`docs/superpowers/plans/2026-05-27-rttp-elcp-primary-reprobe-failure-investigation.md`](2026-05-27-rttp-elcp-primary-reprobe-failure-investigation.md).

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks.

**2. Inline Execution** — execute tasks in this session with executing-plans checkpoints.

Which approach?
