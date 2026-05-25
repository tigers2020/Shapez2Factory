# PR-2d — Throughput-Aware Placement Goals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect `throughput_target_percent` → `placement_goal_count` → `select_genome` so RTTP attempts enough route-feasible bundles to meet `target_throughput_per_min`, and when it cannot, emit explicit `throughput_shortfall_reason` without HUD greenwash.

**Architecture:** Pure `placement_goal.py` computes caps and `placement_goal_count` after candidate generation inside `pipeline.py`; `greedy_regret` / `macro_greedy_regret` accept explicit `goal_count`; `solver_runtime_entry` passes `target_throughput_per_min` + parsed `max_placement_goal_count` via `RttpPipelineConfig`; `rttp_solver_summary` deprecates `capacity_satisfied` for UI pass and adds `throughput_goal` blob.

**Tech Stack:** Django 5.x, `Decimal`, `math.ceil`, StrEnum, pytest-django, ruff, gettext/`shapezUiT`

**Spec:** [`docs/superpowers/specs/2026-05-24-throughput-target-selection-pr2d-design.md`](../specs/2026-05-24-throughput-target-selection-pr2d-design.md)

**Depends on:** PR-2b `actual_committed_output_per_min` · PR-2c `throughput_target_percent` + budget fields on `master` (or rebase branch)

**Branch:** `feat/asteroid-lab-throughput-target-selection-pr2d` (worktree recommended)

**Out of scope:** PR-2d.1 greedy score tuning · `capacity_goals` skeleton rewrite · transport grid install

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `django_apps/asteroid_lab/services/placement_goal.py` | Caps, `placement_goal_count`, shortfall enum + attribution |
| Create | `tests/unit/asteroid_lab/test_placement_goal.py` | Pure policy tests (120 vs 480 fixture pins) |
| Create | `tests/unit/asteroid_lab/test_throughput_shortfall.py` | Attribution priority tests |
| Modify | `django_apps/asteroid_lab/services/solver_run_config_keys.py` | `max_placement_goal_count` key |
| Modify | `django_apps/asteroid_lab/optimization/input_contracts.py` | `RttpPipelineConfig.target_throughput_per_min`, `max_placement_goal_count` |
| Modify | `django_apps/asteroid_lab/optimization/selection/greedy_regret.py` | `goal_count` parameter |
| Modify | `django_apps/asteroid_lab/optimization/selection/macro_greedy_regret.py` | Same `goal_count` |
| Modify | `django_apps/asteroid_lab/optimization/pipeline.py` | Compute plan after pool; record metrics on selection step |
| Modify | `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | `throughput_goal`, deprecated capacity fields |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Parse max goal; pass target into pipeline config |
| Modify | `django_apps/asteroid_lab/services/solver_run_lab_summary.py` | Nested `throughput_goal` DTO |
| Modify | `django_apps/web/views/public_pages.py` | Fail-closed POST validation |
| Modify | `django_apps/asteroid_lab/management/commands/run_solver.py` | `--max-placement-goal-count` |
| Modify | `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Budget pass chip; no `capacity_satisfied` green |
| Modify | `tests/unit/asteroid_lab/test_rttp_greedy_regret.py` | `goal_count=13` selection |
| Modify | `tests/unit/asteroid_lab/test_rttp_solver_summary.py` | Deprecated capacity + `throughput_goal` |
| Modify | `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` | DTO fields |
| Modify | `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | PR-2d status line |

---

### Task 1: Config key + `placement_goal.py` (TDD)

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_config_keys.py`
- Create: `django_apps/asteroid_lab/services/placement_goal.py`
- Create: `tests/unit/asteroid_lab/test_placement_goal.py`

- [ ] **Step 1: Add config key**

```python
# solver_run_config_keys.py
SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY = "max_placement_goal_count"
```

Export in `__all__`.

- [ ] **Step 2: Write failing tests**

```python
# tests/unit/asteroid_lab/test_placement_goal.py
from decimal import Decimal

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.placement_goal import (
    DEFAULT_MAX_PLACEMENT_GOAL_COUNT,
    MAX_MAX_PLACEMENT_GOAL_COUNT,
    MIN_MAX_PLACEMENT_GOAL_COUNT,
    ThroughputShortfallReason,
    build_placement_goal_plan,
    parse_max_placement_goal_count,
)


def _candidate(
    anchor: tuple[int, int],
    *,
    factor: int,
    reachable: bool = True,
) -> BundleCandidate:
    from django_apps.asteroid_lab.optimization.candidates.pattern_library import (
        build_pattern_library,
    )

    pattern = next(p for p in build_pattern_library() if p.pattern_id == "lin_e_len0")
    occupied = frozenset((anchor[0] + dx, anchor[1] + dy) for dx, dy in pattern.occupied_offsets)
    stub = (anchor[0] + pattern.output_stub_offset[0], anchor[1] + pattern.output_stub_offset[1])
    return BundleCandidate(
        candidate_id=f"{anchor[0]},{anchor[1]}:lin_e_len0:shape_belt",
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=factor,
        route_probe_cost=5,
        reachable=reachable,
    )


def test_parse_max_placement_goal_defaults_to_32() -> None:
    assert parse_max_placement_goal_count({}) == 32


def test_parse_max_placement_goal_rejects_0() -> None:
    with pytest.raises(ValueError, match="1"):
        parse_max_placement_goal_count({"max_placement_goal_count": 0})


def test_parse_max_placement_goal_rejects_129() -> None:
    with pytest.raises(ValueError, match="128"):
        parse_max_placement_goal_count({"max_placement_goal_count": 129})


def test_reference_slug_plan_factor4_only(monkeypatch) -> None:
    """Ops regression: best=120, bundles_needed=13, placement_goal=13 when caps allow."""

    from django_apps.game_data.models.mining import MiningExtractionRule

    rule = MiningExtractionRule(
        resource_kind="shape",
        mini_unit_output_per_min=Decimal("30"),
        max_extension_count=3,
        is_active=True,
    )

    def fake_get_active_rule(resource_kind: str) -> MiningExtractionRule:
        assert resource_kind == "shape"
        return rule

    monkeypatch.setattr(
        "django_apps.game_data.services.mining_extraction_rules.get_active_rule",
        fake_get_active_rule,
    )

    normals = tuple(_candidate((i, 0), factor=4) for i in range(20))
    plan = build_placement_goal_plan(
        normal_candidates=normals,
        transport_kind=TransportKind.SHAPE_BELT,
        target_throughput_per_min=Decimal("1536"),
        skeleton_capacity_goals=1,
        configured_max_placement_goal=32,
    )
    assert plan.best_bundle_throughput_per_min == Decimal("120")
    assert plan.bundles_needed_for_target == 13
    assert plan.placement_goal_count == 13


def test_plan_uses_factor16_when_reachable(monkeypatch) -> None:
    from django_apps.game_data.models.mining import MiningExtractionRule

    rule = MiningExtractionRule(
        resource_kind="shape",
        mini_unit_output_per_min=Decimal("30"),
        max_extension_count=3,
        is_active=True,
    )

    monkeypatch.setattr(
        "django_apps.game_data.services.mining_extraction_rules.get_active_rule",
        lambda _: rule,
    )

    normals = (
        _candidate((0, 0), factor=4),
        _candidate((5, 0), factor=16),
    )
    plan = build_placement_goal_plan(
        normal_candidates=normals,
        transport_kind=TransportKind.SHAPE_BELT,
        target_throughput_per_min=Decimal("1536"),
        skeleton_capacity_goals=1,
        configured_max_placement_goal=32,
    )
    assert plan.best_bundle_throughput_per_min == Decimal("480")
    assert plan.bundles_needed_for_target == 4
```

- [ ] **Step 3: Run — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_placement_goal.py -v --tb=short
```

- [ ] **Step 4: Implement `placement_goal.py`**

```python
"""Throughput-aware placement goal policy (PR-2d; never replay input)."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.optimization.selection.equivalence import dedupe_candidates
from django_apps.asteroid_lab.services.committed_throughput_summary import (
    resource_kind_for_transport,
)
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import decimal_str
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY,
)

MIN_MAX_PLACEMENT_GOAL_COUNT = 1
MAX_MAX_PLACEMENT_GOAL_COUNT = 128
DEFAULT_MAX_PLACEMENT_GOAL_COUNT = 32


class ThroughputShortfallReason(StrEnum):
    SATISFIED = "satisfied"
    ROUTE_FEASIBLE_CANDIDATE_CAP = "route_feasible_candidate_cap"
    NON_OVERLAPPING_ANCHOR_CAP = "non_overlapping_anchor_cap"
    COMMIT_CONFLICT_CAP = "commit_conflict_cap"
    SELECTION_GOAL_CAP = "selection_goal_cap"
    CANDIDATE_POOL_EXHAUSTED = "candidate_pool_exhausted"
    BEST_BUNDLE_ZERO = "best_bundle_zero"
    NO_ACTUAL_OUTPUT = "no_actual_output"


@dataclass(frozen=True, slots=True)
class PlacementGoalPlan:
    placement_goal_count: int
    bundles_needed_for_target: int
    best_bundle_throughput_per_min: Decimal
    route_feasible_candidate_cap: int
    non_overlapping_anchor_cap: int
    configured_max_placement_goal: int
    skeleton_capacity_goals: int

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "placement_goal_count": self.placement_goal_count,
            "bundles_needed_for_target": self.bundles_needed_for_target,
            "best_bundle_throughput_per_min": decimal_str(self.best_bundle_throughput_per_min),
            "route_feasible_candidate_cap": self.route_feasible_candidate_cap,
            "non_overlapping_anchor_cap": self.non_overlapping_anchor_cap,
            "configured_max_placement_goal": self.configured_max_placement_goal,
            "skeleton_capacity_goals": self.skeleton_capacity_goals,
        }


def parse_max_placement_goal_count(config: Mapping[str, Any]) -> int:
    raw = config.get(
        SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY,
        DEFAULT_MAX_PLACEMENT_GOAL_COUNT,
    )
    if isinstance(raw, bool) or not isinstance(raw, int):
        msg = "max_placement_goal_count must be an integer"
        raise ValueError(msg)
    if raw < MIN_MAX_PLACEMENT_GOAL_COUNT or raw > MAX_MAX_PLACEMENT_GOAL_COUNT:
        msg = (
            f"max_placement_goal_count must be between "
            f"{MIN_MAX_PLACEMENT_GOAL_COUNT} and {MAX_MAX_PLACEMENT_GOAL_COUNT}"
        )
        raise ValueError(msg)
    return raw


def _best_bundle_throughput(
    *,
    normal_candidates: Sequence[BundleCandidate],
    transport_kind: TransportKind,
) -> Decimal:
    from django_apps.game_data.services.mining_extraction_rules import (
        get_active_rule,
        output_per_min,
    )

    reachable = [c for c in normal_candidates if c.reachable]
    if not reachable:
        return Decimal(0)
    rule = get_active_rule(resource_kind_for_transport(transport_kind))
    return max(output_per_min(rule, c.throughput_factor) for c in reachable)


def build_placement_goal_plan(
    *,
    normal_candidates: Sequence[BundleCandidate],
    transport_kind: TransportKind,
    target_throughput_per_min: Decimal,
    skeleton_capacity_goals: int,
    configured_max_placement_goal: int,
) -> PlacementGoalPlan:
    reachable = [c for c in normal_candidates if c.reachable]
    route_cap = len(reachable)
    deduped = dedupe_candidates(tuple(reachable))
    anchor_cap = len({c.anchor_coord for c in deduped})
    best = _best_bundle_throughput(
        normal_candidates=normal_candidates,
        transport_kind=transport_kind,
    )
    if best <= 0:
        bundles_needed = 0
    else:
        bundles_needed = int(
            (target_throughput_per_min / best).to_integral_value(rounding="ROUND_CEILING")
        )
        # use math.ceil on Decimal quotient for portability:
        bundles_needed = math.ceil(float(target_throughput_per_min / best))

    floor = max(0, skeleton_capacity_goals)
    raw_goal = max(floor, bundles_needed)
    placement_goal_count = min(
        route_cap,
        anchor_cap,
        configured_max_placement_goal,
        raw_goal,
    )
    return PlacementGoalPlan(
        placement_goal_count=placement_goal_count,
        bundles_needed_for_target=bundles_needed,
        best_bundle_throughput_per_min=best,
        route_feasible_candidate_cap=route_cap,
        non_overlapping_anchor_cap=anchor_cap,
        configured_max_placement_goal=configured_max_placement_goal,
        skeleton_capacity_goals=skeleton_capacity_goals,
    )
```

Fix `ROUND_CEILING` in implementation to use `decimal ROUND_CEILING` like PR-2c — adjust in code review step.

- [ ] **Step 5: Run — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_placement_goal.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/placement_goal.py
```

---

### Task 2: Shortfall attribution (TDD)

**Files:**
- Modify: `django_apps/asteroid_lab/services/placement_goal.py` (add `attribute_throughput_shortfall`)
- Create: `tests/unit/asteroid_lab/test_throughput_shortfall.py`

- [ ] **Step 1: Failing tests**

```python
# tests/unit/asteroid_lab/test_throughput_shortfall.py
from decimal import Decimal

from django_apps.asteroid_lab.services.placement_goal import (
    PlacementGoalPlan,
    ThroughputShortfallReason,
    attribute_throughput_shortfall,
)


def _plan(**kwargs) -> PlacementGoalPlan:
    defaults = dict(
        placement_goal_count=13,
        bundles_needed_for_target=13,
        best_bundle_throughput_per_min=Decimal("120"),
        route_feasible_candidate_cap=127,
        non_overlapping_anchor_cap=42,
        configured_max_placement_goal=32,
        skeleton_capacity_goals=1,
    )
    defaults.update(kwargs)
    return PlacementGoalPlan(**defaults)


def test_cap_reason_before_conflict() -> None:
    reason = attribute_throughput_shortfall(
        plan=_plan(placement_goal_count=3, bundles_needed_for_target=13),
        selected_count=3,
        committed_count=3,
        conflict_count=0,
        budget_satisfied=False,
        actual=Decimal("360"),
        target=Decimal("1536"),
    )
    assert reason == ThroughputShortfallReason.SELECTION_GOAL_CAP


def test_conflict_only_when_selection_reached_goal() -> None:
    reason = attribute_throughput_shortfall(
        plan=_plan(),
        selected_count=13,
        committed_count=8,
        conflict_count=5,
        budget_satisfied=False,
        actual=Decimal("960"),
        target=Decimal("1536"),
    )
    assert reason == ThroughputShortfallReason.COMMIT_CONFLICT_CAP
```

- [ ] **Step 2: Implement `attribute_throughput_shortfall`** per spec §5 priority (impossible pool → selection cap → commit conflict → throughput short at full count).

- [ ] **Step 3: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_throughput_shortfall.py -v --tb=short
```

---

### Task 3: `select_genome` explicit `goal_count`

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/selection/greedy_regret.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_greedy_regret.py`

- [ ] **Step 1: Add optional `goal_count: int | None = None` to `select_genome`**

```python
def select_genome(
    normal_candidates: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    *,
    config: SelectionConfig | None = None,
    goal_count: int | None = None,
) -> PlacementGenome:
    resolved = config if config is not None else SelectionConfig()
    pool = list(dedupe_candidates(normal_candidates))
    commit_order: list[str] = []
    committed_occupied: set[Coord] = set()
    committed_route_cells: set[Coord] = set()
    resolved_goal = (
        max(0, goal_count)
        if goal_count is not None
        else max(0, skeleton.capacity_goals)
    )
    while pool and len(commit_order) < resolved_goal:
        ...
```

- [ ] **Step 2: Test — 15 non-overlapping anchors, `goal_count=13` → `len(commit_order)==13`**

Use distinct anchors like `test_rttp_greedy_regret.py` `_bundle_candidate` helper.

- [ ] **Step 3: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_greedy_regret.py -v --tb=short
```

---

### Task 4: Pipeline wiring + `RttpPipelineConfig`

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/input_contracts.py`
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py`
- Modify: `django_apps/asteroid_lab/optimization/selection/macro_greedy_regret.py`

- [ ] **Step 1: Extend `RttpPipelineConfig`**

```python
@dataclass(frozen=True, slots=True)
class RttpPipelineConfig:
    macro_only_mode: bool = False
    ...
    target_throughput_per_min: Decimal | None = None
    max_placement_goal_count: int = DEFAULT_MAX_PLACEMENT_GOAL_COUNT
```

Import `DEFAULT_MAX_PLACEMENT_GOAL_COUNT` from `placement_goal` or duplicate constant in config module (prefer import from services).

- [ ] **Step 2: In `_run_v01_rttp_pipeline` after candidate generation**

```python
from django_apps.asteroid_lab.services.placement_goal import build_placement_goal_plan

placement_plan = None
selection_goal = skeleton.capacity_goals
if config.target_throughput_per_min is not None:
    placement_plan = build_placement_goal_plan(
        normal_candidates=generation.normal_candidates,
        transport_kind=inp.transport_kind,
        target_throughput_per_min=config.target_throughput_per_min,
        skeleton_capacity_goals=skeleton.capacity_goals,
        configured_max_placement_goal=config.max_placement_goal_count,
    )
    selection_goal = placement_plan.placement_goal_count

genome = select_genome(
    generation.normal_candidates,
    skeleton,
    inp,
    goal_count=selection_goal,
)
```

- [ ] **Step 3: Add `placement_plan` metrics to `rttp.genome_selection` step `metrics_json`**

```python
"selected_count": len(genome.commit_order),
"placement_goal_count": selection_goal,
```

Include `placement_plan.to_summary_dict()` when not None.

- [ ] **Step 4: Mirror in macro path** — pass `goal_count=selection_goal` into `select_macro_genome` (add parameter same as v0.1).

- [ ] **Step 5: Run RTTP unit tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_greedy_regret.py tests/unit/asteroid_lab/test_rttp_commit.py tests/unit/asteroid_lab/test_rttp_pipeline_catalog_audit.py -v --tb=short
```

---

### Task 5: `solver_runtime_entry` + config parse

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Modify: `django_apps/asteroid_lab/management/commands/run_solver.py`
- Modify: `django_apps/web/views/public_pages.py`
- Create: `tests/unit/web/test_asteroid_run_solver_max_placement_goal.py` (or extend existing config test file)

- [ ] **Step 1: Parse `max_placement_goal_count` fail-closed** alongside throughput percent (reuse `SolverRuntimeEntryErrorCode` — add `INVALID_MAX_PLACEMENT_GOAL_COUNT` if missing).

- [ ] **Step 2: After `build_reconstruction_capacity_envelope` and `parse_throughput_target_percent`, compute target Decimal and pass into `_rttp_pipeline_config_from_run_config`:**

```python
target_dec = compute_target_throughput_per_min(
    reconstruction_max=primary_reconstruction_max_per_min(capacity_env),
    percent=throughput_percent,
)
return RttpPipelineConfig(
    ...,
    target_throughput_per_min=target_dec,
    max_placement_goal_count=parse_max_placement_goal_count(run_config),
)
```

- [ ] **Step 3: After pipeline, call `attribute_throughput_shortfall` and merge into `build_rttp_solver_summary` kwargs** (`throughput_goal_plan`, `selected_count`, `committed_count`, `conflict_count`, budget fields).

- [ ] **Step 4: HTTP/CLI tests for invalid 0 / 129**

---

### Task 6: `rttp_solver_summary` + HUD honesty

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/rttp_solver_summary.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_solver_summary.py`
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`
- Modify: `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

- [ ] **Step 1: Extend `build_rttp_solver_summary` signature**

```python
def build_rttp_solver_summary(
    *,
    ...
    throughput_goal: Mapping[str, Any] | None = None,
    throughput_shortfall_reason: str | None = None,
) -> dict[str, Any]:
```

- [ ] **Step 2: Set deprecated fields**

```python
budget_ok = bool(throughput_budget_fields.get("throughput_budget_satisfied")) if throughput_budget_fields else pipeline_ok
summary["capacity_satisfied"] = budget_ok  # false when budget fails even if validation passed
summary["placement_capacity_satisfied"] = _placement_capacity_dev_metric(...)
```

When `throughput_budget_fields` present and `validation_passed` true but budget false: `capacity_satisfied` must be **false**.

- [ ] **Step 3: Nest `throughput_goal` + `issue_details`**

```python
if throughput_goal is not None:
    summary["throughput_goal"] = dict(throughput_goal)
    if throughput_shortfall_reason and not budget_ok:
        summary.setdefault("issue_codes", [])
        if "throughput_target_shortfall" not in summary["issue_codes"]:
            summary["issue_codes"].append("throughput_target_shortfall")
        summary["issue_details"] = [
            {
                "code": "throughput_target_shortfall",
                "throughput_shortfall_reason": throughput_shortfall_reason,
            }
        ]
```

- [ ] **Step 4: Test**

```python
def test_capacity_satisfied_false_when_validation_ok_budget_fail() -> None:
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=1,
        normal_count=127,
        commit_order=("a",),
        algorithm_steps=[],
        throughput_budget_fields={
            "throughput_budget_satisfied": False,
            "target_throughput_per_min": "1536.0000",
            "actual_committed_output_per_min": "120.0000",
        },
    )
    assert summary["validation_passed"] is True
    assert summary["capacity_satisfied"] is False
    assert summary["throughput_budget_satisfied"] is False
```

- [ ] **Step 5: Lab JS — replace `capacity_satisfied` green checks for throughput card with `throughput_budget_satisfied`**

Search `asteroid_miner_layout_lab.js` for `capacity_satisfied` in chip/success helpers; update budget card only (do not break validation-failed styling).

- [ ] **Step 6: `solver_run_lab_summary` — expose `throughput_goal` nested object in Detail C section builder.

---

### Task 7: Docs + narrow gate

**Files:**
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`
- Modify: `docs/superpowers/specs/2026-05-24-throughput-target-percent-pr2c-design.md` (one-line PR-2d pointer if missing)

- [ ] **Step 1: Roadmap Axis A — PR-2d in flight / CLOSED when merged**

- [ ] **Step 2: Full narrow gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_placement_goal.py tests/unit/asteroid_lab/test_throughput_shortfall.py tests/unit/asteroid_lab/test_rttp_greedy_regret.py tests/unit/asteroid_lab/test_rttp_solver_summary.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/placement_goal.py django_apps/asteroid_lab/optimization/selection/greedy_regret.py django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/optimization/rttp_solver_summary.py django_apps/asteroid_lab/services/solver_runtime_entry.py
```

---

### Task 8: Ops smoke (manual — primary pass A)

- [ ] **Step 1: Run solver on reference slug**

```powershell
python manage.py run_solver --slug <reference-slug> --throughput-target-percent 10
```

- [ ] **Step 2: Record in plan close note**

| Field | Expected |
|-------|----------|
| `throughput_goal.placement_goal_count` | `13` when anchor_cap ≥ 13 |
| `best_bundle_throughput_per_min` | `120.0000` if no reachable x16 |
| Primary pass | `actual >= 1536` OR explicit `throughput_shortfall_reason` |
| HUD | No green budget chip when `throughput_budget_satisfied` false |

---

## Plan self-review (spec coverage)

| Spec section | Task |
|--------------|------|
| §2 Primary / fail-but-correct | Task 6, 8 |
| §4 placement_goal_count formula | Task 1, 4 |
| §5 Shortfall enum + priority | Task 2, 5, 6 |
| §6 Deprecated capacity fields | Task 6 |
| §7 Config fail-closed | Task 1, 5 |
| §8 Tests | Tasks 1–7 |
| Appendix slug arithmetic | Task 1 test + Task 8 |

No TBD placeholders in task steps.

---

## Execution handoff

Plan saved to [`docs/superpowers/plans/2026-05-24-throughput-target-selection-pr2d.md`](2026-05-24-throughput-target-selection-pr2d.md).

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session with executing-plans checkpoints  

Which approach do you want?
