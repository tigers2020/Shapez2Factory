# Deferred Commit Retry Shadow PR-1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add observe-only `DeferredRetryShadowSummary` diagnostics after primary `incremental_commit` and before LNS, with output-only pipeline step and pytest contracts — zero commit/validation/LNS behavior change.

**Architecture:** Pure builder in `optimization/commit/deferred_retry_shadow.py` reads `CommitResult` + `PlacementGenome.commit_order` + `candidates_by_id` only. `pipeline.py` snapshots `primary_commit_result`, appends `rttp.deferred_commit_retry_shadow` step, then runs LNS unchanged. Metrics JSON is a projection; DTO is canonical.

**Tech Stack:** Python 3.12+, dataclasses, `StrEnum`, Django asteroid_lab optimization package, pytest, ruff, mypy

**Spec:** [`docs/superpowers/specs/2026-05-24-deferred-commit-retry-shadow-pr1-design.md`](../specs/2026-05-24-deferred-commit-retry-shadow-pr1-design.md)

**Worktree:** Implement on a feature branch from current `master` after decontamination baseline green.

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `django_apps/asteroid_lab/contracts/deferred_retry_shadow.py` | Frozen DTOs + config defaults |
| Create | `django_apps/asteroid_lab/optimization/commit/deferred_retry_shadow.py` | Pure builder + metrics projection |
| Modify | `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | `RTTP_DEFERRED_COMMIT_RETRY_SHADOW` step id |
| Modify | `django_apps/asteroid_lab/optimization/pipeline.py` | Primary snapshot + append step before LNS |
| Modify | `django_apps/asteroid_lab/optimization/input_contracts.py` | `DeferredRetryShadowConfig` on `RttpPipelineConfig` |
| Create | `tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py` | PR-1 contract tests |
| Modify | `tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py` | Assert shadow step present (smoke) |
| Modify | `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | PR-1 row (in progress → CLOSED when done) |
| Modify | `documents/ai/current_plan.md` | Next focus sub-bullet when PR-1 merges |

**Out of scope PR-1:** `incremental_commit.py` loop changes, `local_lns.py`, macro pipeline, new replay event enum (use step `event_type` string only).

---

### Task 0: Baseline gate (BLOCK if red)

**Files:** none

- [ ] **Step 1: Sync and run standing gates**

```powershell
git checkout master
git pull
powershell -File scripts/test_quarantine_registry.ps1
powershell -File scripts/test_optimization_contamination.ps1
powershell -File scripts/test_reconstruction_narrow.ps1
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
```

Expected: all PASS. If any FAIL, **BLOCKED** — do not start PR-1 until baseline green.

- [ ] **Step 2: Confirm spec on disk**

```powershell
Test-Path docs/superpowers/specs/2026-05-24-deferred-commit-retry-shadow-pr1-design.md
```

Expected: `True`.

---

### Task 1: Contract DTOs

**Files:**
- Create: `django_apps/asteroid_lab/contracts/deferred_retry_shadow.py`
- Test: `tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py`

- [ ] **Step 1: Write failing import test**

```python
# tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py (append at top of file as first test)

from django_apps.asteroid_lab.contracts.deferred_retry_shadow import (
    DeferredRetryShadowBudget,
    DeferredRetryShadowCandidate,
    DeferredRetryShadowConfig,
    DeferredRetryShadowSummary,
    PRIMARY_INCREMENTAL_COMMIT_PHASE,
)


def test_deferred_retry_shadow_contract_imports() -> None:
    assert PRIMARY_INCREMENTAL_COMMIT_PHASE == "primary_incremental_commit"
    assert DeferredRetryShadowConfig().enabled is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py::test_deferred_retry_shadow_contract_imports -v --tb=short`

Expected: FAIL `ModuleNotFoundError` or import error.

- [ ] **Step 3: Implement contract module**

```python
# django_apps/asteroid_lab/contracts/deferred_retry_shadow.py
"""Deferred commit retry shadow contracts (PR-1 observe-only)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

PRIMARY_INCREMENTAL_COMMIT_PHASE: Literal["primary_incremental_commit"] = (
    "primary_incremental_commit"
)


@dataclass(frozen=True, slots=True)
class DeferredRetryShadowConfig:
    """PR-1 defaults; PR-2 may wire from RttpPipelineConfig."""

    enabled: bool = True
    observe_only: bool = True
    max_retry_rounds: int = 1
    max_candidates: int | None = None  # None => no extra cap beyond eligible set
    route_probe_max_expansions: int = 500


@dataclass(frozen=True, slots=True)
class DeferredRetryShadowBudget:
    max_retry_rounds: int
    max_candidates: int
    route_probe_max_expansions: int


@dataclass(frozen=True, slots=True)
class DeferredRetryShadowCandidate:
    candidate_id: str
    conflict_reason: str  # CommitConflictReason.value from primary pass
    original_commit_order: int
    transport_kind: str
    domain_snapshot_index: int
    retry_round: int  # PR-1 always 0 (queued for round 1, not executed)


@dataclass(frozen=True, slots=True)
class DeferredRetryShadowSummary:
    enabled: bool
    observe_only: bool
    source_phase: Literal["primary_incremental_commit"]
    candidate_count: int
    candidates: tuple[DeferredRetryShadowCandidate, ...]
    budget: DeferredRetryShadowBudget
    domain_context: Mapping[str, Any]
    ineligible_conflict_count: int


__all__ = [
    "PRIMARY_INCREMENTAL_COMMIT_PHASE",
    "DeferredRetryShadowBudget",
    "DeferredRetryShadowCandidate",
    "DeferredRetryShadowConfig",
    "DeferredRetryShadowSummary",
]
```

- [ ] **Step 4: Run import test**

Run: `python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py::test_deferred_retry_shadow_contract_imports -v --tb=short`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/contracts/deferred_retry_shadow.py tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py
git commit -m "feat(asteroid-lab): add deferred retry shadow contract DTOs"
```

---

### Task 2: Pure builder

**Files:**
- Create: `django_apps/asteroid_lab/optimization/commit/deferred_retry_shadow.py`
- Modify: `tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py`

- [ ] **Step 1: Write failing builder tests (narrow corridor)**

```python
from django_apps.asteroid_lab.optimization.commit.deferred_retry_shadow import (
    build_deferred_retry_shadow_summary,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.contracts.deferred_retry_shadow import (
    DeferredRetryShadowConfig,
    PRIMARY_INCREMENTAL_COMMIT_PHASE,
)
from tests.support.rttp_narrow_corridor_fixture import (
    NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
    NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID,
    build_narrow_corridor_optimization_input,
    candidate_by_id,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from django_apps.asteroid_lab.optimization.input_contracts import RttpSkeletonConfig


def test_deferred_shadow_records_reprobe_failed_after_primary_commit(
    narrow_corridor_optimization_input,
) -> None:
    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp, skeleton, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM
    )
    first = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    second = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID)
    genome = PlacementGenome(
        commit_order=(first.candidate_id, second.candidate_id),
    )
    candidates_by_id = {
        first.candidate_id: first,
        second.candidate_id: second,
    }
    domain = initial_commit_domain(skeleton, inp)
    primary = incremental_commit(
        genome, candidates_by_id, inp, skeleton, domain=domain
    )
    shadow = build_deferred_retry_shadow_summary(
        primary_commit_result=primary,
        commit_order=genome.commit_order,
        candidates_by_id=candidates_by_id,
        inp=inp,
        config=DeferredRetryShadowConfig(),
    )
    assert shadow.source_phase == PRIMARY_INCREMENTAL_COMMIT_PHASE
    assert shadow.observe_only is True
    assert shadow.candidate_count == 1
    assert len(shadow.candidates) == 1
    row = shadow.candidates[0]
    assert row.candidate_id == second.candidate_id
    assert row.conflict_reason == CommitConflictReason.REPROBE_FAILED.value
    assert row.original_commit_order == 1
    assert row.domain_snapshot_index == 1
```

Add fixture reuse: copy `narrow_corridor_optimization_input` fixture from `test_rttp_commit_survivability.py` or import pytest fixture from that module if already shared; otherwise duplicate the `@pytest.fixture` definition in this test file.

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py::test_deferred_shadow_records_reprobe_failed_after_primary_commit -v --tb=short`

Expected: FAIL (builder missing).

- [ ] **Step 3: Implement builder**

```python
# django_apps/asteroid_lab/optimization/commit/deferred_retry_shadow.py
"""Observe-only deferred commit retry shadow (PR-1)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.asteroid_lab.contracts.deferred_retry_shadow import (
    PRIMARY_INCREMENTAL_COMMIT_PHASE,
    DeferredRetryShadowBudget,
    DeferredRetryShadowCandidate,
    DeferredRetryShadowConfig,
    DeferredRetryShadowSummary,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflict,
    CommitConflictReason,
    CommitResult,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput


def _commits_before(
    candidate_id: str,
    commit_order: Sequence[str],
    committed_ids: frozenset[str],
) -> int:
    count = 0
    for cid in commit_order:
        if cid == candidate_id:
            break
        if cid in committed_ids:
            count += 1
    return count


def _eligible_conflicts(
    conflicts: tuple[CommitConflict, ...],
) -> tuple[CommitConflict, ...]:
    return tuple(
        c
        for c in conflicts
        if c.reason is CommitConflictReason.REPROBE_FAILED
    )


def build_deferred_retry_shadow_summary(
    *,
    primary_commit_result: CommitResult,
    commit_order: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
    inp: OptimizationInput,
    config: DeferredRetryShadowConfig | None = None,
) -> DeferredRetryShadowSummary:
    """Pure summary of who would enter a deferred retry queue (no probe, no commit)."""

    resolved = config or DeferredRetryShadowConfig()
    if not resolved.enabled:
        empty_budget = DeferredRetryShadowBudget(
            max_retry_rounds=resolved.max_retry_rounds,
            max_candidates=0,
            route_probe_max_expansions=resolved.route_probe_max_expansions,
        )
        return DeferredRetryShadowSummary(
            enabled=False,
            observe_only=resolved.observe_only,
            source_phase=PRIMARY_INCREMENTAL_COMMIT_PHASE,
            candidate_count=0,
            candidates=(),
            budget=empty_budget,
            domain_context=_domain_context(primary_commit_result, inp, eligible_count=0),
            ineligible_conflict_count=len(primary_commit_result.conflicts),
        )

    committed_set = frozenset(primary_commit_result.committed_ids)
    order_index = {cid: idx for idx, cid in enumerate(commit_order)}
    eligible = _eligible_conflicts(primary_commit_result.conflicts)
    rows: list[DeferredRetryShadowCandidate] = []
    for conflict in eligible:
        idx = order_index.get(conflict.candidate_id)
        if idx is None:
            continue
        candidate = candidates_by_id.get(conflict.candidate_id)
        if candidate is None:
            continue
        rows.append(
            DeferredRetryShadowCandidate(
                candidate_id=conflict.candidate_id,
                conflict_reason=conflict.reason.value,
                original_commit_order=idx,
                transport_kind=candidate.transport_kind.value,
                domain_snapshot_index=_commits_before(
                    conflict.candidate_id,
                    commit_order,
                    committed_set,
                ),
                retry_round=0,
            )
        )
    rows.sort(key=lambda r: (r.original_commit_order, r.candidate_id))
    cap = resolved.max_candidates
    if cap is not None and len(rows) > cap:
        rows = rows[:cap]
    budget = DeferredRetryShadowBudget(
        max_retry_rounds=resolved.max_retry_rounds,
        max_candidates=len(rows),
        route_probe_max_expansions=resolved.route_probe_max_expansions,
    )
    ineligible = len(primary_commit_result.conflicts) - len(eligible)
    return DeferredRetryShadowSummary(
        enabled=True,
        observe_only=resolved.observe_only,
        source_phase=PRIMARY_INCREMENTAL_COMMIT_PHASE,
        candidate_count=len(rows),
        candidates=tuple(rows),
        budget=budget,
        domain_context=_domain_context(
            primary_commit_result,
            inp,
            eligible_count=len(rows),
        ),
        ineligible_conflict_count=ineligible,
    )


def _domain_context(
    primary_commit_result: CommitResult,
    inp: OptimizationInput,
    *,
    eligible_count: int,
) -> dict[str, Any]:
    return {
        "primary_commit_domain_version": primary_commit_result.domain_version,
        "primary_committed_count": len(primary_commit_result.committed_ids),
        "primary_conflict_count": len(primary_commit_result.conflicts),
        "eligible_reprobe_failed_count": eligible_count,
        "transport_kind": inp.transport_kind.value,
    }


def deferred_retry_shadow_metrics(
    summary: DeferredRetryShadowSummary,
) -> dict[str, Any]:
    """JSON-serializable projection for algorithm_steps (output-only)."""

    return {
        "source_phase": summary.source_phase,
        "observe_only": summary.observe_only,
        "enabled": summary.enabled,
        "candidate_count": summary.candidate_count,
        "eligible_candidate_ids": [c.candidate_id for c in summary.candidates],
        "ineligible_conflict_count": summary.ineligible_conflict_count,
        "budget": {
            "max_retry_rounds": summary.budget.max_retry_rounds,
            "max_candidates": summary.budget.max_candidates,
            "route_probe_max_expansions": summary.budget.route_probe_max_expansions,
        },
        "domain_context": dict(summary.domain_context),
        "candidates": [
            {
                "candidate_id": c.candidate_id,
                "conflict_reason": c.conflict_reason,
                "original_commit_order": c.original_commit_order,
                "transport_kind": c.transport_kind,
                "domain_snapshot_index": c.domain_snapshot_index,
                "retry_round": c.retry_round,
            }
            for c in summary.candidates
        ],
    }


__all__ = [
    "build_deferred_retry_shadow_summary",
    "deferred_retry_shadow_metrics",
]
```

- [ ] **Step 4: Add remaining builder unit tests**

```python
import ast
from pathlib import Path
from unittest.mock import patch

import pytest

from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflict,
    CommitConflictReason,
    CommitResult,
)
from django_apps.asteroid_lab.optimization.commit import deferred_retry_shadow as shadow_mod
from django_apps.asteroid_lab.optimization.routing import route_probe


def test_deferred_shadow_ignores_non_reprobe_conflicts() -> None:
    primary = CommitResult(
        committed_ids=(),
        reserved_route_cells=frozenset(),
        domain_version=0,
        conflicts=(
            CommitConflict("c1", CommitConflictReason.OCCUPIED_CELL_CONFLICT),
            CommitConflict("c2", CommitConflictReason.REPROBE_FAILED),
        ),
    )
    summary = shadow_mod.build_deferred_retry_shadow_summary(
        primary_commit_result=primary,
        commit_order=("c1", "c2"),
        candidates_by_id={},
        inp=pytest.importorskip("tests.support.rttp_narrow_corridor_fixture")  # use real inp fixture instead
    )
```

**Fix the above test** — do not use `pytest.importorskip` hack. Use `narrow_corridor_optimization_input` fixture and real `candidates_by_id` for `c2` only; assert `candidate_count == 1` and `ineligible_conflict_count == 1`.

```python
def test_deferred_shadow_candidate_order_is_deterministic() -> None:
    primary = CommitResult(
        committed_ids=("a",),
        reserved_route_cells=frozenset(),
        domain_version=1,
        conflicts=(
            CommitConflict("z", CommitConflictReason.REPROBE_FAILED),
            CommitConflict("m", CommitConflictReason.REPROBE_FAILED),
        ),
    )
    # candidates_by_id with transport_kind on BundleCandidate stubs — use replace() on narrow fixture candidates
    # assert shadow.candidates[0].candidate_id == "m" before "z" by original_commit_order
```

```python
def test_deferred_shadow_does_not_call_route_probe() -> None:
    with patch.object(route_probe, "probe_route") as spy:
        # call build_deferred_retry_shadow_summary with minimal CommitResult
        ...
    spy.assert_not_called()
```

```python
_REPO = Path(__file__).resolve().parents[3]
_SHADOW = _REPO / "django_apps/asteroid_lab/optimization/commit/deferred_retry_shadow.py"


def test_deferred_shadow_module_has_no_forbidden_imports() -> None:
    tree = ast.parse(_SHADOW.read_text(encoding="utf-8-sig"))
    imports = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]
    assert "django_apps.asteroid_lab.replay" not in imports
    assert not any("solver_summary" in (m or "") for m in imports)
    assert "route_probe" not in imports
```

```python
def test_deferred_shadow_records_budget_and_domain_context(
    narrow_corridor_optimization_input,
) -> None:
    # reuse primary commit from first test; assert budget.max_retry_rounds == 1
    # assert domain_context["primary_commit_domain_version"] >= 1
```

- [ ] **Step 5: Run builder tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py -v --tb=short`

Expected: all PASS

- [ ] **Step 6: Ruff on new files**

Run: `python -m ruff check django_apps/asteroid_lab/contracts/deferred_retry_shadow.py django_apps/asteroid_lab/optimization/commit/deferred_retry_shadow.py tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add django_apps/asteroid_lab/optimization/commit/deferred_retry_shadow.py tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py
git commit -m "feat(asteroid-lab): add pure deferred retry shadow builder"
```

---

### Task 3: Pipeline step + step id

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/rttp_solver_summary.py`
- Modify: `django_apps/asteroid_lab/optimization/input_contracts.py`
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py`

- [ ] **Step 1: Write failing pipeline test**

```python
# tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py (add)

from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId


def test_pipeline_includes_deferred_retry_shadow_step_after_primary_commit(
    greenfield_optimization_input,
) -> None:
    from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
        ExtractorPlacementPolicy,
    )
    from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline

    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    step_ids = [row["step_id"] for row in result.algorithm_steps]
    assert RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value in step_ids
    shadow_idx = step_ids.index(
        RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value
    )
    commit_idx = step_ids.index(RttpAlgorithmStepId.RTTP_COMMIT.value)
    assert shadow_idx < commit_idx
    shadow_row = next(
        row
        for row in result.algorithm_steps
        if row["step_id"]
        == RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value
    )
    assert shadow_row["passed"] is True
    assert shadow_row["metrics"]["source_phase"] == "primary_incremental_commit"
    assert shadow_row["metrics"]["observe_only"] is True
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py::test_pipeline_includes_deferred_retry_shadow_step_after_primary_commit -v --tb=short`

Expected: FAIL (step missing).

- [ ] **Step 3: Add step id enum member**

In `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` inside `RttpAlgorithmStepId`:

```python
RTTP_DEFERRED_COMMIT_RETRY_SHADOW = "rttp.deferred_commit_retry_shadow"
```

- [ ] **Step 4: Add config field**

In `django_apps/asteroid_lab/optimization/input_contracts.py`:

```python
from django_apps.asteroid_lab.contracts.deferred_retry_shadow import DeferredRetryShadowConfig

@dataclass(frozen=True, slots=True)
class RttpPipelineConfig:
    macro_only_mode: bool = False
    allow_singleton_genome_slots: bool = False
    max_macro_candidates: int = 64
    catalog_placement_validation_mode: CatalogValidationMode = "mapped_fail_closed"
    deferred_retry_shadow: DeferredRetryShadowConfig = field(
        default_factory=DeferredRetryShadowConfig
    )
```

Add `from dataclasses import field` if not present.

- [ ] **Step 5: Wire pipeline (v0.1 path only)**

In `django_apps/asteroid_lab/optimization/pipeline.py`:

1. Imports:

```python
from django_apps.asteroid_lab.contracts.deferred_retry_shadow import DeferredRetryShadowConfig
from django_apps.asteroid_lab.optimization.commit.deferred_retry_shadow import (
    build_deferred_retry_shadow_summary,
    deferred_retry_shadow_metrics,
)
```

2. Add helper (mirror `_append_catalog_placement_audit_step`):

```python
def _append_deferred_retry_shadow_step(
    steps: list[dict[str, Any]],
    *,
    shadow_config: DeferredRetryShadowConfig,
    primary_commit_result: CommitResult,
    commit_order: Sequence[str],
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
) -> None:
    summary = build_deferred_retry_shadow_summary(
        primary_commit_result=primary_commit_result,
        commit_order=commit_order,
        candidates_by_id=candidates_by_id,
        inp=inp,
        config=shadow_config,
    )
    metrics = deferred_retry_shadow_metrics(summary)
    steps.append(
        algorithm_step_summary_to_json(
            {
                "step_id": RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value,
                "phase": "incremental_commit",
                "event_type": "rttp.deferred_commit_retry_shadow",
                "title": "Deferred commit retry shadow (observe-only)",
                "summary": (
                    "Primary-pass deferred retry queue shadow; no retry executed."
                ),
                "metrics": metrics,
                "passed": True,
            }
        )
    )
```

3. In `_run_v01_rttp_pipeline` replace:

```python
    commit_result = incremental_commit(...)
    if commit_result.conflicts:
        genome, commit_result = run_local_lns(...)
```

with:

```python
    primary_commit_result = incremental_commit(
        genome,
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
    )
    _append_deferred_retry_shadow_step(
        steps,
        shadow_config=config.deferred_retry_shadow,
        primary_commit_result=primary_commit_result,
        commit_order=genome.commit_order,
        candidates_by_id=candidates_by_id,
        inp=inp,
    )
    commit_result = primary_commit_result
    if primary_commit_result.conflicts:
        genome, commit_result = run_local_lns(
            inp,
            skeleton,
            genome,
            candidates_by_id,
            primary_commit_result,
            policy=policy,
        )
```

**Do not** change macro path `_run_macro_rttp_pipeline` in PR-1.

- [ ] **Step 6: Run pipeline + shadow tests**

Run:

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py::test_pipeline_includes_deferred_retry_shadow_step_after_primary_commit -v --tb=short
```

Expected: PASS

- [ ] **Step 7: LNS ordering / immutability test**

```python
def test_deferred_shadow_runs_before_lns_and_unchanged_by_lns(
    narrow_corridor_optimization_input,
) -> None:
    from django_apps.asteroid_lab.optimization import pipeline as pipeline_mod

    captured: dict[str, object] = {}

    def _fake_lns(inp, skeleton, genome, candidates_by_id, commit_result, **kwargs):
        captured["eligible_at_lns_entry"] = [
            c.candidate_id
            for c in commit_result.conflicts
            if c.reason == CommitConflictReason.REPROBE_FAILED
        ]
        return genome, commit_result

    with patch.object(pipeline_mod, "run_local_lns", side_effect=_fake_lns):
        result = pipeline_mod.run_rttp_pipeline(
            narrow_corridor_optimization_input,
            policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        )
    shadow = next(
        row
        for row in result.algorithm_steps
        if row["step_id"]
        == RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value
    )
    assert shadow["metrics"]["candidate_count"] >= 1
    assert captured["eligible_at_lns_entry"]
    assert shadow["metrics"]["eligible_candidate_ids"]
```

Place in `test_deferred_commit_retry_shadow.py`.

- [ ] **Step 8: Commit unchanged CommitResult identity test**

```python
def test_deferred_shadow_does_not_change_commit_result(
    narrow_corridor_optimization_input,
) -> None:
    # run incremental_commit once; build shadow; assert primary committed_ids/conflicts unchanged
```

- [ ] **Step 9: Commit**

```bash
git add django_apps/asteroid_lab/optimization/rttp_solver_summary.py django_apps/asteroid_lab/optimization/input_contracts.py django_apps/asteroid_lab/optimization/pipeline.py tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py
git commit -m "feat(asteroid-lab): record deferred retry shadow before LNS"
```

---

### Task 4: Regression gates + docs

**Files:**
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Full narrow regression**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py tests/unit/asteroid_lab/test_rttp_commit_survivability.py tests/unit/asteroid_lab/test_rttp_lns.py tests/unit/asteroid_lab/test_validation_readonly_guards.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
python -m ruff check django_apps/asteroid_lab/contracts/deferred_retry_shadow.py django_apps/asteroid_lab/optimization/commit/deferred_retry_shadow.py django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/optimization/input_contracts.py django_apps/asteroid_lab/optimization/rttp_solver_summary.py
python -m mypy django_apps/asteroid_lab/contracts/deferred_retry_shadow.py django_apps/asteroid_lab/optimization/commit/deferred_retry_shadow.py
```

Expected: all PASS.

- [ ] **Step 2: Optional ops spot-check**

```powershell
python manage.py run_solver --slug copy-import-495e552c
```

Inspect latest `SolverRun.config_json["solver_summary"]["algorithm_steps"]` for `step_id == "rttp.deferred_commit_retry_shadow"`. Record note in PR body only — not a merge blocker if slug DB missing locally.

- [ ] **Step 3: Update roadmap row**

Under Axis B or new “Deferred commit retry” subsection add:

```markdown
| PR-1 shadow (observe-only) | 🔄 / ✅ | spec + plan links; merge SHA when done |
```

- [ ] **Step 4: Commit docs**

```bash
git add docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md documents/ai/current_plan.md docs/superpowers/specs/2026-05-24-deferred-commit-retry-shadow-pr1-design.md
git commit -m "docs: add deferred commit retry shadow PR-1 spec and roadmap row"
```

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| §1 primary-only before LNS | Task 3 pipeline wiring + Task 3 Step 7 test |
| §2 INV-PR1-01 observe-only | Task 2 pure builder; Task 3 no commit mutation |
| §2 INV-PR1-04 no route probe | Task 2 `test_deferred_shadow_does_not_call_route_probe` |
| §2 INV-PR1-05 REPROBE_FAILED only | Task 2 eligibility + ignore test |
| §2 INV-PR1-06 budget recorded | Task 1 DTO + Task 2 metrics |
| §2 INV-PR1-07 domain context | `_domain_context` in builder |
| §2 INV-PR1-08 ordering | sort in builder + deterministic test |
| §2 INV-PR1-09 LNS separation | Task 3 Step 7 |
| Step id + output-only | Task 3 enum + metrics projection |
| Macro out of scope | Plan file map explicit |
| Contamination gates | Task 4 Step 1 |

No TBD placeholders remain in task code blocks (engineer must replace the one noted `importorskip` anti-pattern in Step 4 with fixture-based test).

---

## PR body template

```markdown
## Summary
- Observe-only deferred commit retry shadow after primary incremental_commit (before LNS).
- Pure `DeferredRetryShadowSummary` DTO; pipeline step `rttp.deferred_commit_retry_shadow`.
- No commit, LNS, validation, or route_domain behavior change.

## Test plan
- [ ] pytest test_deferred_commit_retry_shadow.py
- [ ] pytest test_rttp_pipeline_greenfield (shadow step ordering)
- [ ] test_rttp_commit_survivability + test_rttp_lns
- [ ] scripts/test_optimization_contamination.ps1
- [ ] rttp narrow gate
```
