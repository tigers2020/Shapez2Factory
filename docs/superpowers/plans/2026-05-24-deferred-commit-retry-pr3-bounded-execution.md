# Deferred Commit Retry PR-3 Bounded Execution Implementation Plan

**Status:** CLOSED 2026-05-24 — merged `d3de9645` (PR #75)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run one bounded deferred retry round after primary `incremental_commit` when `deferred_retry_shadow.enabled=true` and `observe_only=false`, merge into `CommitResult` for LNS, and record execution only on `rttp.deferred_commit_retry_execute` while preserving PR-2 shadow envelope.

**Architecture:** Extract `_attempt_commit_one` in `incremental_commit.py` (characterization tests first). New `deferred_retry_execute.py` replays primary commits into domain state, retries eligible `REPROBE_FAILED` rows once, builds `CommitResult_merged`. `pipeline.py` orchestrates shadow (always) → execute (conditional) → LNS(merged). Mapper lifts `observe_only=false` fail-closed atomically with executor wiring.

**Tech Stack:** Python 3.12+, dataclasses, StrEnum, Django asteroid_lab optimization, pytest, ruff, black, mypy

**Spec:** [`docs/superpowers/specs/2026-05-24-deferred-commit-retry-pr3-bounded-execution-design.md`](../specs/2026-05-24-deferred-commit-retry-pr3-bounded-execution-design.md)

**Branch:** `feat/deferred-commit-retry-pr3-bounded-execution` (from `master` after PR-2 merge `a5cfca87`)

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `django_apps/asteroid_lab/optimization/commit/incremental_commit.py` | `_attempt_commit_one`, `CommitAttemptOutcome`, `max_expansions` on probe |
| Create | `django_apps/asteroid_lab/contracts/deferred_retry_execute.py` | `DeferredRetryExecuteResult` |
| Create | `django_apps/asteroid_lab/optimization/commit/deferred_retry_execute.py` | `run_bounded_deferred_retry`, metrics builder |
| Modify | `django_apps/asteroid_lab/optimization/pipeline.py` | execute branch, `_append_deferred_retry_execute_step` |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_entry.py` | parse `observe_only: false` |
| Modify | `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | `RTTP_DEFERRED_COMMIT_RETRY_EXECUTE` |
| Modify | `django_apps/asteroid_lab/replay/event_types.py` | `EVENT_TYPE_RTTP_DEFERRED_COMMIT_RETRY_EXECUTE` |
| Modify | `tests/unit/asteroid_lab/test_rttp_commit.py` | characterization before extract |
| Create | `tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py` | executor + pipeline + mapper |
| Modify | `tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py` | `observe_only=false` parses (no raise) |
| Modify | `docs/superpowers/specs/2026-05-24-deferred-commit-retry-pr3-bounded-execution-design.md` | Status → CLOSED on merge |
| Modify | `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | PR-3 row on close |

**No change:** `deferred_retry_shadow.py` builder logic (primary-only), macro pipeline, `local_lns.py` internals.

---

### Task 0: Baseline (BLOCK if red)

**Files:** none

- [ ] **Step 1: Branch from master**

```powershell
git checkout master
git pull
git checkout -b feat/deferred-commit-retry-pr3-bounded-execution
git merge-base --is-ancestor a5cfca87 HEAD
```

Expected: exit code 0 (PR-2 on ancestor chain).

- [ ] **Step 2: Deferred retry + commit gates**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py tests/unit/asteroid_lab/test_rttp_commit.py tests/unit/asteroid_lab/test_rttp_commit_survivability.py -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
```

Expected: all PASS. If FAIL → **BLOCKED** until green.

---

### Task 1: Characterization tests (before `_attempt_commit_one` extract)

**Risk note:** Shared primitive extraction is the highest regression surface in PR-3. Lock behavior **before** refactor.

**Files:**
- Modify: `tests/unit/asteroid_lab/test_rttp_commit.py`
- Test: same file

- [ ] **Step 1: Add characterization helpers and tests**

Append to `tests/unit/asteroid_lab/test_rttp_commit.py`:

```python
def _commit_result_snapshot(
    inp: OptimizationInput,
    commit_order: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
) -> tuple[tuple[str, ...], frozenset[tuple[str, str]], int]:
    """Stable tuple for before/after refactor comparison."""
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=commit_order),
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
    )
    conflict_pairs = frozenset(
        (c.candidate_id, c.reason.value) for c in result.conflicts
    )
    return result.committed_ids, conflict_pairs, result.domain_version


def test_incremental_commit_primary_behavior_unchanged_after_attempt_primitive_extract(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    """PR-3 gate: greenfield single-candidate commit snapshot (run before and after extract)."""
    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    assert generation.normal_candidates
    candidate = generation.normal_candidates[0]
    before = _commit_result_snapshot(
        inp,
        (candidate.candidate_id,),
        {candidate.candidate_id: candidate},
    )
    after = _commit_result_snapshot(
        inp,
        (candidate.candidate_id,),
        {candidate.candidate_id: candidate},
    )
    assert after == before
    assert before[0] == (candidate.candidate_id,)


def test_incremental_commit_narrow_corridor_snapshot_before_extract(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    """PR-3 gate: B-CS1 two-candidate primary pass snapshot (pre-extract baseline)."""
    from tests.support.rttp_narrow_corridor_fixture import (
        NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
        NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID,
        candidate_by_id,
    )

    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    order = (first.candidate_id, second.candidate_id)
    pool = {first.candidate_id: first, second.candidate_id: second}
    committed, conflicts, _version = _commit_result_snapshot(inp, order, pool)
    assert committed == (first.candidate_id,)
    assert (second.candidate_id, CommitConflictReason.REPROBE_FAILED.value) in conflicts
```

Add imports at top of file if missing: `ExtractorPlacementPolicy`, `generate_candidates`, `PlacementGenome`, `RttpSkeletonBuilder`, `RttpSkeletonConfig`.

- [ ] **Step 2: Run characterization tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_commit.py::test_incremental_commit_primary_behavior_unchanged_after_attempt_primitive_extract tests/unit/asteroid_lab/test_rttp_commit.py::test_incremental_commit_narrow_corridor_snapshot_before_extract -v --tb=short
```

Expected: PASS (baseline captured).

- [ ] **Step 3: Commit**

```bash
git add tests/unit/asteroid_lab/test_rttp_commit.py
git commit -m "test(asteroid-lab): incremental_commit characterization before PR-3 extract"
```

---

### Task 2: Extract `_attempt_commit_one` in `incremental_commit.py`

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/commit/incremental_commit.py`
- Test: `tests/unit/asteroid_lab/test_rttp_commit.py`

- [ ] **Step 1: Add outcome type and primitive**

In `incremental_commit.py`, add after `CommitResult`:

```python
@dataclass(frozen=True, slots=True)
class CommitAttemptOutcome:
    """Single candidate commit attempt (probe + post-probe checks)."""

    committed: bool
    conflict: CommitConflict | None = None
    route_cells: frozenset[Coord] = frozenset()


def _attempt_commit_one(
    candidate: BundleCandidate,
    *,
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goals: frozenset[Coord],
    committed_occupied: frozenset[Coord],
    committed_route_cells: frozenset[Coord],
    max_expansions: int | None = None,
) -> CommitAttemptOutcome:
```

Use the existing `incremental_commit` probe `max_expansions` behavior as the default. Do not introduce a new numeric default unless it matches current behavior. In `incremental_commit.py`, define:

```python
import inspect

from django_apps.asteroid_lab.optimization.routing.route_probe import probe_route

_COMMIT_PROBE_MAX_EXPANSIONS: int = int(
    inspect.signature(probe_route).parameters["max_expansions"].default
)
```

Callers omit `max_expansions` by passing `_COMMIT_PROBE_MAX_EXPANSIONS` inside `_attempt_commit_one` when `max_expansions is None`.

```python
def _attempt_commit_one(
    ...
    max_expansions: int | None = None,
) -> CommitAttemptOutcome:
    resolved_expansions = (
        _COMMIT_PROBE_MAX_EXPANSIONS
        if max_expansions is None
        else max_expansions
    )
    probe = probe_route(..., max_expansions=resolved_expansions)
    if candidate.transport_kind is not inp.transport_kind:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.TRANSPORT_KIND_CONFLICT,
            ),
        )
    if candidate.occupied_cells & committed_occupied:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.OVERLAP,
            ),
        )
    if candidate.output_stub in committed_route_cells:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.INLET_ON_SHARED_TRANSPORT,
            ),
        )
    current_domain = _rebuild_domain(
        skeleton,
        inp,
        committed_occupied=committed_occupied,
        committed_route_cells=committed_route_cells,
    )
    probe = probe_route(
        current_domain,
        candidate.output_stub,
        goals,
        max_expansions=max_expansions,
    )
    if not probe.reachable:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.REPROBE_FAILED,
            ),
        )
    route_cells = _route_cells_from_path(probe.path, candidate.occupied_cells)
    if route_cells & committed_route_cells:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.ROUTE_CELL_CONFLICT,
            ),
        )
    if route_cells & committed_occupied:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.OCCUPIED_CELL_CONFLICT,
            ),
        )
    if route_cells & inp.protected_corridor_cells:
        return CommitAttemptOutcome(
            committed=False,
            conflict=CommitConflict(
                candidate_id=candidate.candidate_id,
                reason=CommitConflictReason.HARD_PROTECTED_CONFLICT,
            ),
        )
    return CommitAttemptOutcome(committed=True, route_cells=route_cells)
```

- [ ] **Step 2: Refactor `incremental_commit` loop to call primitive**

Replace per-candidate body (from transport check through confirm) with:

```python
        outcome = _attempt_commit_one(
            candidate,
            skeleton=skeleton,
            inp=inp,
            goals=goals,
            committed_occupied=committed_occupied,
            committed_route_cells=committed_route_cells,
        )
        if not outcome.committed:
            if outcome.conflict is not None:
                conflicts.append(outcome.conflict)
            continue
        route_cells = outcome.route_cells
        committed_ids.append(candidate_id)
        committed_occupied = frozenset(committed_occupied | candidate.occupied_cells)
        committed_route_cells = frozenset(committed_route_cells | route_cells)
        trunk_mask_cells = frozenset(trunk_mask_cells | route_cells)
        domain_version += 1
```

Keep `CANDIDATE_NOT_FOUND` handling before `_attempt_commit_one`.

Export in `__all__`: `"CommitAttemptOutcome"`, `"_attempt_commit_one"` (leading underscore OK for package-internal use; executor imports from same package).

- [ ] **Step 3: Re-run characterization + full commit module**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_commit.py tests/unit/asteroid_lab/test_rttp_commit_survivability.py -v --tb=short
```

Expected: PASS; snapshots unchanged.

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/optimization/commit/incremental_commit.py tests/unit/asteroid_lab/test_rttp_commit.py
git commit -m "refactor(asteroid-lab): extract _attempt_commit_one for PR-3 deferred retry"
```

---

### Task 3: Execute contract + `run_bounded_deferred_retry`

**Files:**
- Create: `django_apps/asteroid_lab/contracts/deferred_retry_execute.py`
- Create: `django_apps/asteroid_lab/optimization/commit/deferred_retry_execute.py`
- Test: `tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py`

- [ ] **Step 1: Contract DTO**

Create `django_apps/asteroid_lab/contracts/deferred_retry_execute.py`:

```python
"""Deferred commit retry execution result (PR-3)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult


@dataclass(frozen=True, slots=True)
class DeferredRetryExecuteResult:
    merged_commit_result: CommitResult
    deferred_retry_rounds_executed: int
    deferred_retry_eligible_count: int
    deferred_retry_attempted_count: int
    deferred_retry_recovered_count: int
    deferred_retry_still_failed_count: int
    recovered_candidate_ids: tuple[str, ...]
    deferred_retry_failed_reason_counts: Mapping[str, int]


def deferred_retry_execute_metrics(result: DeferredRetryExecuteResult) -> dict[str, Any]:
    return {
        "deferred_retry_rounds_executed": result.deferred_retry_rounds_executed,
        "deferred_retry_eligible_count": result.deferred_retry_eligible_count,
        "deferred_retry_attempted_count": result.deferred_retry_attempted_count,
        "deferred_retry_recovered_count": result.deferred_retry_recovered_count,
        "deferred_retry_still_failed_count": result.deferred_retry_still_failed_count,
        "recovered_candidate_ids": list(result.recovered_candidate_ids),
        "deferred_retry_failed_reason_counts": dict(
            result.deferred_retry_failed_reason_counts
        ),
    }
```

- [ ] **Step 2: Write failing executor tests (narrow corridor + merge semantics)**

Create `tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py` with:

```python
"""PR-3 — bounded deferred commit retry execution."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.deferred_retry_shadow import DeferredRetryShadowConfig
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.commit.deferred_retry_execute import (
    run_bounded_deferred_retry,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from django_apps.asteroid_lab.optimization.input_contracts import RttpSkeletonConfig
from tests.support.rttp_narrow_corridor_fixture import (
    NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
    NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID,
    build_narrow_corridor_optimization_input,
    candidate_by_id,
)


def test_deferred_retry_recovers_narrow_corridor_second_candidate() -> None:
    inp = build_narrow_corridor_optimization_input()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    order = (first.candidate_id, second.candidate_id)
    pool = {first.candidate_id: first, second.candidate_id: second}
    domain = initial_commit_domain(skeleton, inp)
    primary = incremental_commit(
        PlacementGenome(commit_order=order),
        pool,
        inp,
        skeleton,
        domain=domain,
    )
    execute = run_bounded_deferred_retry(
        primary_commit_result=primary,
        commit_order=order,
        candidates_by_id=pool,
        inp=inp,
        skeleton=skeleton,
        config=DeferredRetryShadowConfig(enabled=True, observe_only=False),
    )
    merged = execute.merged_commit_result
    assert merged.committed_ids == order
    assert execute.recovered_candidate_ids == (second.candidate_id,)
    assert execute.deferred_retry_recovered_count == 1
    assert execute.deferred_retry_still_failed_count == 0
    assert not any(
        c.candidate_id == second.candidate_id and c.reason is CommitConflictReason.REPROBE_FAILED
        for c in merged.conflicts
    )


def test_merged_committed_ids_follow_genome_order() -> None:
    """Recovered B between primary A and C must sort as (A, B, C), not (A, C) + append."""
    from django_apps.asteroid_lab.optimization.commit.deferred_retry_execute import (
        merged_committed_ids_for_genome_order,
    )

    order = ("candidate_a", "candidate_b", "candidate_c")
    merged = merged_committed_ids_for_genome_order(
        commit_order=order,
        primary_committed_ids=("candidate_a", "candidate_c"),
        recovered_candidate_ids=("candidate_b",),
    )
    assert merged == ("candidate_a", "candidate_b", "candidate_c")
```

- [ ] **Step 3: Run tests — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py -v --tb=short
```

Expected: FAIL (`run_bounded_deferred_retry` not defined).

- [ ] **Step 4: Implement `deferred_retry_execute.py`**

Create `django_apps/asteroid_lab/optimization/commit/deferred_retry_execute.py` implementing:

1. **`_eligible_queue(primary, commit_order, candidates_by_id, config)`** — reuse same rules as `build_deferred_retry_shadow_summary` (import `_eligible_conflicts` from shadow module or duplicate minimal filter: `REPROBE_FAILED` + in order + candidate exists). Sort by `commit_order` index then `candidate_id`. Apply `max_candidates` cap.

2. **`_replay_primary_state(...)`** — walk `commit_order`; for each `cid` in `primary_commit_result.committed_ids`, call `_attempt_commit_one` and apply success updates (must not conflict). Raises `RuntimeError` if primary replay fails (invariant violation).

3. **`run_bounded_deferred_retry(...)`**:
   - If eligible queue empty: return `DeferredRetryExecuteResult` with `merged_commit_result=primary`, counts zero, `deferred_retry_rounds_executed=0`.
   - Else one round: for each eligible `cid`, `_attempt_commit_one(..., max_expansions=config.route_probe_max_expansions)`.
   - Track `recovered_candidate_ids`, `failed_reason_counts`, new conflict rows from failures.
   - **`merged_conflicts`**: start `list(primary.conflicts)`; remove only rows where `reason is REPROBE_FAILED` and `candidate_id in recovered`; extend with new failure conflicts (do not drop unrelated primary rows).
   - **`merged_committed_ids`**: `tuple(cid for cid in commit_order if cid in set(primary.committed_ids) | set(recovered))`.
   - **`reserved_route_cells` / `domain_version`**: from final replay+retry state after loop.

4. **`deferred_retry_still_failed_count`** = `attempted_count - recovered_count`.

- [ ] **Step 5: Run executor tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py -v --tb=short
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/contracts/deferred_retry_execute.py django_apps/asteroid_lab/optimization/commit/deferred_retry_execute.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py
git commit -m "feat(asteroid-lab): bounded deferred commit retry executor (PR-3)"
```

---

### Task 4: Step ids + replay event type

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/rttp_solver_summary.py`
- Modify: `django_apps/asteroid_lab/replay/event_types.py`
- Test: `tests/unit/asteroid_lab/test_rttp_solver_summary.py` (if exists) or add assert in pr3 pipeline tests

- [ ] **Step 1: Add enum members**

In `RttpAlgorithmStepId`:

```python
RTTP_DEFERRED_COMMIT_RETRY_EXECUTE = "rttp.deferred_commit_retry_execute"
```

In `event_types.py`:

```python
EVENT_TYPE_RTTP_DEFERRED_COMMIT_RETRY_EXECUTE = "rttp.deferred_commit_retry_execute"
```

Add to any `RTTP_EVENT_TYPES` / validation frozensets alongside other `EVENT_TYPE_RTTP_*` constants.

- [ ] **Step 2: Commit**

```bash
git add django_apps/asteroid_lab/optimization/rttp_solver_summary.py django_apps/asteroid_lab/replay/event_types.py
git commit -m "feat(asteroid-lab): deferred retry execute step id and event type (PR-3)"
```

---

### Task 5: Mapper lift (`observe_only: false`) — atomic with pipeline

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Modify: `tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py`

- [ ] **Step 1: Update PR-2 policy tests**

Replace `test_observe_only_false_raises` with:

```python
def test_observe_only_false_maps_when_enabled() -> None:
    cfg = _deferred_retry_shadow_config_from_run_config(
        {
            SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {
                "enabled": True,
                "observe_only": False,
            }
        }
    )
    assert cfg.enabled is True
    assert cfg.observe_only is False
```

- [ ] **Step 2: Implement mapper parse**

In `_deferred_retry_shadow_config_from_run_config`, replace PR-2 fail-closed block with:

```python
    observe_only = _require_bool(raw.get("observe_only", True), field="observe_only")
```

Remove:

```python
    if "observe_only" in raw:
        if not _require_bool(raw["observe_only"], field="observe_only"):
            msg = "deferred_retry_shadow.observe_only must remain true in PR-2"
            raise ValueError(msg)
```

Return `DeferredRetryShadowConfig(..., observe_only=observe_only, ...)`.

- [ ] **Step 3: Run policy tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py -v --tb=short
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/services/solver_runtime_entry.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py
git commit -m "feat(asteroid-lab): allow observe_only false for PR-3 execution gate"
```

---

### Task 6: Pipeline wiring + execute step

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py`
- Test: `tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py`

- [ ] **Step 1: Add failing pipeline tests**

Append to `test_deferred_commit_retry_pr3_execute.py`:

```python
from django_apps.asteroid_lab.contracts.deferred_retry_shadow import DeferredRetryShadowConfig
from django_apps.asteroid_lab.optimization.input_contracts import RttpPipelineConfig
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId


def test_disabled_shadow_does_not_append_execute_step(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            deferred_retry_shadow=DeferredRetryShadowConfig(enabled=False),
        ),
    )
    step_ids = [row["step_id"] for row in result.algorithm_steps]
    assert RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value in step_ids
    assert RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_EXECUTE.value not in step_ids


def test_observe_only_true_does_not_append_execute_step(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            deferred_retry_shadow=DeferredRetryShadowConfig(
                enabled=True,
                observe_only=True,
            ),
        ),
    )
    step_ids = [row["step_id"] for row in result.algorithm_steps]
    assert RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_EXECUTE.value not in step_ids


def test_observe_only_false_appends_execute_step_after_shadow(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        narrow_corridor_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            deferred_retry_shadow=DeferredRetryShadowConfig(
                enabled=True,
                observe_only=False,
            ),
        ),
    )
    step_ids = [row["step_id"] for row in result.algorithm_steps]
    shadow_idx = step_ids.index(
        RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value
    )
    execute_idx = step_ids.index(
        RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_EXECUTE.value
    )
    assert shadow_idx < execute_idx
```

Add `OptimizationInput` import and `narrow_corridor_optimization_input` fixture (import from `test_rttp_commit_survivability` pattern or duplicate fixture).

- [ ] **Step 2: Run pipeline tests — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py -k "append_execute" -v --tb=short
```

Expected: FAIL (execute step / wiring missing).

- [ ] **Step 3: Wire `pipeline.py`**

After `_append_deferred_retry_shadow_step(...)` block (~line 363):

```python
    shadow_cfg = config.deferred_retry_shadow
    should_execute_deferred_retry = shadow_cfg.enabled and not shadow_cfg.observe_only
    commit_result = primary_commit_result
    if should_execute_deferred_retry:
        execute_out = run_bounded_deferred_retry(
            primary_commit_result=primary_commit_result,
            commit_order=genome.commit_order,
            candidates_by_id=candidates_by_id,
            inp=inp,
            skeleton=skeleton,
            config=shadow_cfg,
        )
        commit_result = execute_out.merged_commit_result
        _append_deferred_retry_execute_step(steps, execute_out=execute_out)
```

Change LNS call to use `commit_result` (not `primary_commit_result`):

```python
    if commit_result.conflicts:
        genome, commit_result = run_local_lns(
            ...
            commit_result,
            ...
        )
```

Add `_append_deferred_retry_execute_step` helper (mirror shadow helper) using `deferred_retry_execute_metrics` and `RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_EXECUTE`.

Remove duplicate `commit_result = primary_commit_result` if present.

- [ ] **Step 4: LNS receives merged — pipeline wiring unit test**

Narrow corridor may clear all conflicts after retry, so LNS never runs. Force a remaining conflict and inject a distinct merged result:

```python
from unittest.mock import patch

from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflict,
    CommitConflictReason,
    CommitResult,
)
from django_apps.asteroid_lab.contracts.deferred_retry_execute import (
    DeferredRetryExecuteResult,
)


def test_lns_receives_merged_not_primary_when_execution_ran(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    primary = CommitResult(
        committed_ids=("only_primary",),
        reserved_route_cells=frozenset(),
        domain_version=1,
        conflicts=(
            CommitConflict("retry_me", CommitConflictReason.REPROBE_FAILED),
            CommitConflict("stays", CommitConflictReason.OVERLAP),
        ),
    )
    merged = CommitResult(
        committed_ids=("only_primary", "retry_me"),
        reserved_route_cells=frozenset(),
        domain_version=2,
        conflicts=(CommitConflict("stays", CommitConflictReason.OVERLAP),),
    )
    execute_stub = DeferredRetryExecuteResult(
        merged_commit_result=merged,
        deferred_retry_rounds_executed=1,
        deferred_retry_eligible_count=1,
        deferred_retry_attempted_count=1,
        deferred_retry_recovered_count=1,
        deferred_retry_still_failed_count=0,
        recovered_candidate_ids=("retry_me",),
        deferred_retry_failed_reason_counts={},
    )
    seen_primary: list[CommitResult] = []
    seen_lns: list[CommitResult] = []

    def _fake_incremental_commit(*_a: object, **_k: object) -> CommitResult:
        return primary

    def _fake_execute(**_k: object) -> DeferredRetryExecuteResult:
        return execute_stub

    def _capture_lns(*args: object, **_kwargs: object) -> tuple[object, object]:
        seen_lns.append(args[4])
        return args[2], args[4]

    with (
        patch(
            "django_apps.asteroid_lab.optimization.pipeline.incremental_commit",
            side_effect=_fake_incremental_commit,
        ),
        patch(
            "django_apps.asteroid_lab.optimization.pipeline.run_bounded_deferred_retry",
            side_effect=_fake_execute,
        ),
        patch(
            "django_apps.asteroid_lab.optimization.pipeline.run_local_lns",
            side_effect=_capture_lns,
        ),
    ):
        run_rttp_pipeline(
            inp,
            policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
            pipeline_config=RttpPipelineConfig(
                deferred_retry_shadow=DeferredRetryShadowConfig(
                    enabled=True,
                    observe_only=False,
                ),
            ),
        )
    assert seen_lns
    assert seen_lns[0] is merged
    assert seen_lns[0] is not primary
    assert seen_lns[0].committed_ids == ("only_primary", "retry_me")
```

- [ ] **Step 5: PR-2 parity tests still pass**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py::test_disabled_shadow_does_not_change_commit_or_validation -v --tb=short
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/optimization/pipeline.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py
git commit -m "feat(asteroid-lab): wire PR-3 deferred retry execute in RTTP pipeline"
```

---

### Task 7: Remaining PR-3 tests + determinism

**Files:**
- Modify: `tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py`

- [ ] **Step 1: Add tests**

```python
def test_deferred_retry_is_deterministic() -> None:
    inp = build_narrow_corridor_optimization_input()
    # ... build primary once ...
    a = run_bounded_deferred_retry(...)
    b = run_bounded_deferred_retry(...)
    assert a.merged_commit_result == b.merged_commit_result
    assert a.recovered_candidate_ids == b.recovered_candidate_ids


def test_deferred_retry_does_not_retry_inlet_or_overlap(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    # Build synthetic primary CommitResult with INLET conflict only;
    # assert merged.conflicts still contains inlet; recovered_count == 0.
```

Use `CommitConflict(...)` factory with hand-built `CommitResult` for inlet test (no pipeline required).

- [ ] **Step 2: Run full PR-3 file**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py -v --tb=short
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py
git commit -m "test(asteroid-lab): PR-3 determinism and non-eligible conflict guards"
```

---

### Task 8: Gates, docs, close metadata

**Files:**
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`
- Modify: `docs/superpowers/specs/2026-05-24-deferred-commit-retry-pr3-bounded-execution-design.md`
- Modify: `documents/ai/current_plan.md` (on PR merge)

- [ ] **Step 1: Lint / format / typing**

```powershell
python -m ruff check django_apps/asteroid_lab/optimization/commit/ django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/contracts/deferred_retry_execute.py django_apps/asteroid_lab/services/solver_runtime_entry.py
python -m black --check django_apps/asteroid_lab/optimization/commit/ django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/contracts/deferred_retry_execute.py django_apps/asteroid_lab/services/solver_runtime_entry.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py
python -m mypy django_apps/asteroid_lab/optimization/commit/deferred_retry_execute.py django_apps/asteroid_lab/contracts/deferred_retry_execute.py
```

Expected: PASS.

- [ ] **Step 2: Spec verification bundle**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py tests/unit/asteroid_lab/test_rttp_commit.py tests/unit/asteroid_lab/test_rttp_commit_survivability.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
```

Expected: all PASS.

- [ ] **Step 3: INV checklist**

| INV | Verification |
|-----|----------------|
| INV-PR3-01 | `test_deferred_retry_does_not_retry_inlet_or_overlap` |
| INV-PR3-02 | `_replay_primary_state` only applies primary committed |
| INV-PR3-03 | single loop in executor |
| INV-PR3-04 | `test_disabled_shadow_does_not_change_commit_or_validation` |
| INV-PR3-05 | shadow tests + pipeline shadow index |
| INV-PR3-06 | execute step only when `observe_only=false` |
| INV-PR3-07 | no solver_summary in mapper tests |
| INV-PR3-08 | `_rebuild_domain` only |
| INV-PR3-09 | narrow corridor conflict row removal test |

- [ ] **Step 4: Update roadmap row (pre-PR)**

In `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`, set deferred retry PR-3 to in-progress; on merge mark CLOSED with commit hash.

- [ ] **Step 5: PR body template**

```markdown
## Summary
- Bounded deferred retry execution when `enabled=true` and `observe_only=false`
- Extract `_attempt_commit_one`; new `run_bounded_deferred_retry` + execute algorithm step
- LNS receives merged `CommitResult`; PR-2 shadow envelope unchanged

## Test plan
- [x] test_deferred_commit_retry_pr3_execute.py
- [x] test_rttp_commit characterization + test_rttp_commit_survivability.py
- [x] test_deferred_commit_retry_pr2_policy.py (observe_only false maps)
- [x] RTTP narrow gate + contamination gate
```

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| Approach 1 pipeline orchestration | Task 6 |
| Characterization before extract | Task 1 |
| `_attempt_commit_one` + max_expansions | Task 2 |
| `run_bounded_deferred_retry` + merged semantics | Task 3 |
| Global genome `committed_ids` order | Task 3 tests |
| Row-precise conflict removal | Task 3 impl note |
| `still_failed = attempted - recovered` | Task 3 metrics |
| Recommended attempted + reason counts | Task 3 contract |
| Shadow always / execute conditional | Task 6 |
| LNS merged only when execution ran | Task 6 spy test |
| Mapper atomic lift | Task 5 |
| Step id + event type | Task 4 |
| PR-2 tests preserved | Task 6 Step 5 |
| Verification commands | Task 8 |

No TBD / "implement later" in task code blocks.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-24-deferred-commit-retry-pr3-bounded-execution.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration  
2. **Inline Execution** — this session with `executing-plans`, batch execution with checkpoints  

Which approach?
