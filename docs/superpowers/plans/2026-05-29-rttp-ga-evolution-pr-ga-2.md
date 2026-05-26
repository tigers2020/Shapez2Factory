# RTTP GA Evolution PR-GA-2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote bounded GA (`select_genome_evolution`) to optional **primary** genome selector via fail-closed `config_json.selection.mode`, while keeping greedy-regret the default and preserving candidate generation, route probe, incremental commit, and validation contracts.

**Architecture:** Add `SelectionMode` + `RttpPipelineConfig.selection_mode` (default `greedy_regret`). Normal RTTP path calls a single `select_primary_genome` helper that branches to `select_genome` or `select_genome_evolution`. GA operator parameters continue to come from `GaEvolutionShadowConfig` on the pipeline config. Observe-only shadow step remains diagnostic: when primary is evolution and shadow is enabled, compare greedy baseline vs evolution primary (invert PR-GA-1 roles). No new route probe inside GA modules.

**Tech Stack:** Python 3.12+, `StrEnum`, dataclasses, pytest, ruff, black, mypy `django_apps config src`, Django `manage.py run_solver`

**Spec:** [`../specs/2026-05-29-rttp-ga-evolution-design.md`](../specs/2026-05-29-rttp-ga-evolution-design.md) §5 · §2 · §7 PR-GA-2

**Parent plan (PR-GA-1 CLOSED):** [`2026-05-29-rttp-ga-evolution.md`](2026-05-29-rttp-ga-evolution.md)

**Branch:** `feat/rttp-ga-evolution-pr-ga-2` (dedicated worktree recommended)

**Prerequisite:** PR-GA-1 on `master` (PR [#95](https://github.com/tigers2020/Shapez2Factory/pull/95) `5b7ead43`); Capacity C-GATE green (`scripts/test_capacity_sot.ps1`).

---

## Normative invariants (read first — do not violate)

```text
selection.mode changes only genome selection authority.

It must not:
- generate candidates
- run route probe inside GA / genome_fitness / ga_evolution_shadow
- bypass incremental_commit
- mutate validation_passed or validation repair
- read replay / solver_summary / NDJSON as algorithm input
- change macro_only pipeline selection (select_macro_genome path untouched)
```

**Commit authority:**

| `selection.mode` | `incremental_commit` input genome |
|------------------|-----------------------------------|
| `greedy_regret` (default) | `select_genome(...)` |
| `evolution` | `select_genome_evolution(..., config=config.ga_evolution_shadow)` |

Final route proof remains **incremental commit** with latest `route_domain` re-probe per candidate (`test_commit_reprobes_latest_domain` invariant).

**Critical tests (must all exist before PR merge):**

1. Default config → greedy path unchanged vs explicit `greedy_regret`
2. `selection.mode=evolution` → `incremental_commit` receives evolution genome (spy)
3. Invalid `selection.mode` → fail-closed `ValueError`
4. Evolution mode pipeline still records commit step; commit path unchanged (no GA route probe)
5. `test_ga_evolution_no_probe_route` still PASS (architecture)
6. Ops smoke: `copy-import-495e552c` with evolution mode config

---

## File map

| File | Action | Responsibility |
|------|--------|----------------|
| `django_apps/asteroid_lab/contracts/selection_mode.py` | Create | `SelectionMode` StrEnum |
| `django_apps/asteroid_lab/optimization/input_contracts.py` | Modify | `RttpPipelineConfig.selection_mode` |
| `django_apps/asteroid_lab/services/solver_run_config_keys.py` | Modify | `SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY` |
| `django_apps/asteroid_lab/optimization/selection/primary_genome.py` | Create | `select_primary_genome` branch helper |
| `django_apps/asteroid_lab/optimization/pipeline.py` | Modify | Use helper; selection metrics; shadow title/summary when evolution primary |
| `django_apps/asteroid_lab/optimization/selection/ga_evolution_shadow.py` | Modify | Dual-mode shadow summary (greedy baseline vs GA primary) |
| `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Modify | `_selection_mode_from_run_config`; wire `_rttp_pipeline_config_from_run_config` |
| `django_apps/asteroid_lab/management/commands/run_solver.py` | Modify | `--selection-mode` CLI → `config_json.selection` |
| `scripts/run_solver.ps1` | Modify | `-SelectionMode` switch (optional parity) |
| `tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py` | Create | Mapper, primary path, pipeline, frozen default |
| `tests/unit/asteroid_lab/test_ga_evolution_shadow.py` | Modify | Shadow dual-mode + observe_only policy tests |
| `tests/unit/asteroid_lab/test_run_solver_management_command.py` | Modify | CLI persistence |
| `tests/unit/architecture/test_ga_evolution_no_probe_route.py` | Verify | No change unless new GA file added |
| `documents/ai/current_plan.md` | Modify | PR-GA-2 plan link; CLOSED after merge |
| `docs/superpowers/specs/2026-05-29-rttp-ga-evolution-design.md` | Modify | PR-GA-2 status line after approval |
| `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | Modify | Axis A CLOSED on PR-GA-2 merge |

**Out of scope:** macro pipeline GA, LNS/deferred retry behavior, new replay event types, `--config-json-path` generic loader (use normative `--selection-mode` flag like PR-4 deferred retry).

---

## Task 0: Preflight

**Files:** none

- [ ] **Step 1: Confirm PR-GA-1 on `master`**

```powershell
git checkout master
git pull origin master
git log -1 --oneline
```

Expected: ancestor includes PR-GA-1 merge `5b7ead43` (or later).

- [ ] **Step 2: Confirm GA shadow + architecture gates green**

```powershell
python -m pytest tests/unit/asteroid_lab/test_ga_evolution_shadow.py -v --tb=short
python -m pytest tests/unit/architecture/test_ga_evolution_no_probe_route.py -v --tb=short
powershell -File scripts/test_capacity_sot.ps1
```

Expected: all PASS.

- [ ] **Step 3: Baseline RTTP narrow (record count)**

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
```

Expected: PASS — note passed count for Task 8 regression.

- [ ] **Step 4: Confirm canon slug for ops smoke**

```powershell
python manage.py shell -c "from django_apps.asteroid_lab import models as m; p=m.AsteroidProject.objects.filter(slug='copy-import-495e552c').first(); print('project_id', p.pk if p else None)"
```

Expected: positive `project_id`. If `None`, **BLOCKED** until slug restored.

- [ ] **Step 5: Create branch**

```powershell
git checkout -b feat/rttp-ga-evolution-pr-ga-2
```

---

## Task 1: `SelectionMode` contract

**Files:**

- Create: `django_apps/asteroid_lab/contracts/selection_mode.py`
- Modify: `django_apps/asteroid_lab/optimization/input_contracts.py`
- Test: `tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py` (new file)

- [ ] **Step 1: Write failing contract test**

Create `tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py`:

```python
"""PR-GA-2 — config-gated selection.mode primary selector."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from django_apps.asteroid_lab.optimization.input_contracts import RttpPipelineConfig


def test_selection_mode_defaults_greedy_regret() -> None:
    cfg = RttpPipelineConfig()
    assert cfg.selection_mode is SelectionMode.GREEDY_REGRET


def test_selection_mode_enum_values() -> None:
    assert SelectionMode.GREEDY_REGRET.value == "greedy_regret"
    assert SelectionMode.EVOLUTION.value == "evolution"
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py::test_selection_mode_defaults_greedy_regret -v --tb=short
```

Expected: `ModuleNotFoundError` or `AttributeError`

- [ ] **Step 3: Implement contract + pipeline config field**

Create `django_apps/asteroid_lab/contracts/selection_mode.py`:

```python
"""RTTP genome selection mode (PR-GA-2)."""

from __future__ import annotations

from enum import StrEnum


class SelectionMode(StrEnum):
    GREEDY_REGRET = "greedy_regret"
    EVOLUTION = "evolution"


__all__ = ["SelectionMode"]
```

In `django_apps/asteroid_lab/optimization/input_contracts.py`, add import and field on `RttpPipelineConfig`:

```python
from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode

# inside RttpPipelineConfig:
selection_mode: SelectionMode = SelectionMode.GREEDY_REGRET
```

Add `SelectionMode` to `__all__` in `input_contracts.py` if exported.

- [ ] **Step 4: Run contract tests — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py -k "selection_mode" -v --tb=short
```

---

## Task 2: Runtime config mapper (`config_json.selection.mode`)

**Files:**

- Modify: `django_apps/asteroid_lab/services/solver_run_config_keys.py`
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Test: `tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py`

- [ ] **Step 1: Add config key constant**

In `solver_run_config_keys.py`:

```python
SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY = "selection"
```

Add to `__all__`.

- [ ] **Step 2: Write failing mapper tests**

Append to `test_rttp_ga_evolution_pr_ga_2.py`:

```python
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    _rttp_pipeline_config_from_run_config,
    _selection_mode_from_run_config,
)


def test_selection_mode_from_run_config_default() -> None:
    assert _selection_mode_from_run_config({}) is SelectionMode.GREEDY_REGRET


def test_selection_mode_evolution() -> None:
    mode = _selection_mode_from_run_config(
        {SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY: {"mode": "evolution"}}
    )
    assert mode is SelectionMode.EVOLUTION


def test_selection_mode_invalid_raises() -> None:
    with pytest.raises(ValueError, match="selection.mode"):
        _selection_mode_from_run_config(
            {SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY: {"mode": "genetic"}}
        )


def test_pipeline_config_wires_selection_mode() -> None:
    cfg = _rttp_pipeline_config_from_run_config(
        {SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY: {"mode": "evolution"}}
    )
    assert cfg.selection_mode is SelectionMode.EVOLUTION
```

- [ ] **Step 3: Run mapper tests — FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py -k "selection_mode_from_run or pipeline_config_wires" -v --tb=short
```

- [ ] **Step 4: Implement mapper**

In `solver_runtime_entry.py`:

```python
from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY,
    # ... existing imports
)

_VALID_SELECTION_MODES = frozenset({SelectionMode.GREEDY_REGRET.value, SelectionMode.EVOLUTION.value})


def _selection_mode_from_run_config(config: dict[str, Any]) -> SelectionMode:
    raw = config.get(SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY)
    if raw is None:
        return SelectionMode.GREEDY_REGRET
    if not isinstance(raw, dict):
        msg = "selection must be an object"
        raise ValueError(msg)
    mode_raw = raw.get("mode", SelectionMode.GREEDY_REGRET.value)
    if not isinstance(mode_raw, str):
        msg = "selection.mode must be a string"
        raise ValueError(msg)
    if mode_raw not in _VALID_SELECTION_MODES:
        msg = f"selection.mode must be one of {sorted(_VALID_SELECTION_MODES)}"
        raise ValueError(msg)
    return SelectionMode(mode_raw)
```

In `_rttp_pipeline_config_from_run_config`, after `ga_shadow = ...`:

```python
selection_mode = _selection_mode_from_run_config(config)
return RttpPipelineConfig(
    # ... existing fields ...
    ga_evolution_shadow=ga_shadow,
    selection_mode=selection_mode,
)
```

- [ ] **Step 5: Run mapper tests — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py -k "selection_mode" -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/asteroid_lab/contracts/selection_mode.py
```

---

## Task 3: Pipeline primary selection branch

**Files:**

- Create: `django_apps/asteroid_lab/optimization/selection/primary_genome.py`
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py`
- Test: `tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py`

- [ ] **Step 1: Write failing unit test for helper**

Append to `test_rttp_ga_evolution_pr_ga_2.py` (reuse `_bundle_candidate` / `_skeleton_with_goals` from `test_ga_evolution_shadow.py` via import or duplicate minimal factory):

```python
from django_apps.asteroid_lab.contracts.ga_evolution_shadow import GaEvolutionShadowConfig
from django_apps.asteroid_lab.optimization.selection.greedy_regret import select_genome
from django_apps.asteroid_lab.optimization.selection.primary_genome import select_primary_genome
from django_apps.asteroid_lab.optimization.selection.ga_evolution import select_genome_evolution


def test_select_primary_genome_evolution_differs_from_greedy_on_toy_pool(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    # copy _skeleton_with_goals + _bundle_candidate helpers from test_ga_evolution_shadow
    skeleton = _skeleton_with_goals(greenfield_optimization_input, capacity_goals=4)
    pool = tuple(_bundle_candidate((i * 4, 0)) for i in range(4))
    ga_cfg = GaEvolutionShadowConfig(enabled=True, random_seed=11, generations=2, population_size=8)
    greedy = select_primary_genome(
        mode=SelectionMode.GREEDY_REGRET,
        normal_candidates=pool,
        skeleton=skeleton,
        inp=greenfield_optimization_input,
        goal_count=2,
        ga_config=ga_cfg,
    )
    evolved = select_primary_genome(
        mode=SelectionMode.EVOLUTION,
        normal_candidates=pool,
        skeleton=skeleton,
        inp=greenfield_optimization_input,
        goal_count=2,
        ga_config=ga_cfg,
    )
    assert len(evolved.commit_order) <= 2
    # optional: may match on tiny pool — do not require inequality
    assert isinstance(greedy.commit_order, tuple)
```

- [ ] **Step 2: Run test — FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py::test_select_primary_genome_evolution_differs_from_greedy_on_toy_pool -v --tb=short
```

- [ ] **Step 3: Implement `select_primary_genome`**

Create `django_apps/asteroid_lab/optimization/selection/primary_genome.py`:

```python
"""Primary genome selection by SelectionMode (PR-GA-2)."""

from __future__ import annotations

from collections.abc import Sequence

from django_apps.asteroid_lab.contracts.ga_evolution_shadow import GaEvolutionShadowConfig
from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.selection.ga_evolution import select_genome_evolution
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    select_genome,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def select_primary_genome(
    *,
    mode: SelectionMode,
    normal_candidates: Sequence[BundleCandidate],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goal_count: int,
    ga_config: GaEvolutionShadowConfig,
) -> PlacementGenome:
    pool = tuple(normal_candidates)
    if mode is SelectionMode.EVOLUTION:
        return select_genome_evolution(
            pool,
            skeleton,
            inp,
            goal_count=goal_count,
            config=ga_config,
        )
    return select_genome(pool, skeleton, inp, goal_count=goal_count)


__all__ = ["select_primary_genome"]
```

- [ ] **Step 4: Wire pipeline normal path**

In `pipeline.py`, import `SelectionMode`, `select_primary_genome`. Replace:

```python
genome = select_genome(
    generation.normal_candidates,
    skeleton,
    inp,
    goal_count=selection_goal,
)
```

with:

```python
genome = select_primary_genome(
    mode=config.selection_mode,
    normal_candidates=generation.normal_candidates,
    skeleton=skeleton,
    inp=inp,
    goal_count=selection_goal,
    ga_config=config.ga_evolution_shadow,
)
```

Update `selection_metrics`:

```python
selection_metrics: dict[str, Any] = {
    "commit_order": list(genome.commit_order),
    "selected_count": len(genome.commit_order),
    "placement_goal_count": selection_goal,
    "selection_mode": config.selection_mode.value,
}
```

**Do not** change macro-only branch (`select_macro_genome`).

- [ ] **Step 5: Run helper + existing shadow tests — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py tests/unit/asteroid_lab/test_ga_evolution_shadow.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/optimization/selection/primary_genome.py
```

---

## Task 4: Evolution primary integration tests

**Files:**

- Test: `tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py`

- [ ] **Step 1: Default unchanged vs explicit greedy**

```python
def test_default_pipeline_matches_explicit_greedy_mode(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
    from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import ExtractorPlacementPolicy

    baseline = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    explicit = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(selection_mode=SelectionMode.GREEDY_REGRET),
    )
    assert explicit.genome.commit_order == baseline.genome.commit_order
    assert explicit.commit_result.committed_ids == baseline.commit_result.committed_ids
    assert explicit.validation_passed == baseline.validation_passed
```

- [ ] **Step 2: Evolution mode commits evolution genome**

```python
def test_incremental_commit_receives_evolution_genome_when_mode_evolution(
    greenfield_optimization_input: OptimizationInput,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from django_apps.asteroid_lab.optimization.commit.incremental_commit import incremental_commit
    from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
    from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import ExtractorPlacementPolicy

    captured: list[PlacementGenome] = []
    original = incremental_commit

    def _spy(genome: PlacementGenome, *args, **kwargs):
        captured.append(genome)
        return original(genome, *args, **kwargs)

    monkeypatch.setattr(
        "django_apps.asteroid_lab.optimization.pipeline.incremental_commit",
        _spy,
    )
    ga_cfg = GaEvolutionShadowConfig(enabled=True, random_seed=5, generations=2, population_size=8)
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            selection_mode=SelectionMode.EVOLUTION,
            ga_evolution_shadow=ga_cfg,
        ),
    )
    assert len(captured) == 1
    assert captured[0].commit_order == result.genome.commit_order
    selection_step = next(
        row for row in result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_GENOME_SELECTION.value
    )
    assert selection_step["metrics"]["selection_mode"] == "evolution"
```

Add imports: `PlacementGenome`, `RttpAlgorithmStepId`, `RttpPipelineConfig`, `GaEvolutionShadowConfig`.

- [ ] **Step 3: Evolution still reaches commit step (re-probe path alive)**

```python
def test_evolution_mode_pipeline_records_commit_step(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
    from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import ExtractorPlacementPolicy

    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            selection_mode=SelectionMode.EVOLUTION,
            ga_evolution_shadow=GaEvolutionShadowConfig(random_seed=2, generations=1, population_size=6),
        ),
    )
    step_ids = [row["step_id"] for row in result.algorithm_steps]
    assert RttpAlgorithmStepId.RTTP_COMMIT.value in step_ids
    sel_idx = step_ids.index(RttpAlgorithmStepId.RTTP_GENOME_SELECTION.value)
    commit_idx = step_ids.index(RttpAlgorithmStepId.RTTP_COMMIT.value)
    assert sel_idx < commit_idx
```

- [ ] **Step 4: Run Task 4 tests — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py -v --tb=short
```

---

## Task 5: PR-GA-1 shadow policy cleanup

**Files:**

- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Modify: `django_apps/asteroid_lab/optimization/selection/ga_evolution_shadow.py`
- Test: `tests/unit/asteroid_lab/test_ga_evolution_shadow.py`, `test_rttp_ga_evolution_pr_ga_2.py`

**Policy (normative):**

```text
- selection.mode is the ONLY switch for commit authority.
- ga_evolution_shadow.observe_only=false does NOT enable evolution primary.
- ga_evolution_shadow.enabled controls whether the diagnostic shadow STEP runs.
- When selection_mode=evolution and shadow enabled: shadow compares greedy baseline vs evolution primary.
- When selection_mode=greedy_regret and shadow enabled: keep PR-GA-1 behavior (GA proposal vs greedy primary).
```

- [ ] **Step 1: Remove PR-GA-1 observe_only mapper rejection**

In `_ga_evolution_shadow_config_from_run_config`, delete:

```python
if not observe_only:
    msg = "ga_evolution_shadow.observe_only must be true in PR-GA-1"
    raise ValueError(msg)
```

Map `observe_only` with default `True` (field retained for metrics; does not affect commit).

Update `test_ga_evolution_shadow.py`:

- Rename `test_ga_shadow_observe_only_false_raises` → `test_ga_shadow_observe_only_false_allowed_when_not_commit_switch` expecting **no** raise.
- Add assertion: `_rttp_pipeline_config_from_run_config({... observe_only: false ...}).ga_evolution_shadow.observe_only is False` and `selection_mode` still default greedy.

- [ ] **Step 2: Extend `build_ga_evolution_shadow_summary` for dual role**

Add parameter `primary_mode: SelectionMode = SelectionMode.GREEDY_REGRET`.

When `primary_mode is SelectionMode.EVOLUTION` and `config.enabled`:

- `primary_order` = evolution primary genome order (passed in)
- `shadow_order` = `select_genome(...)` greedy baseline (same goal_count)
- Metrics fields unchanged; `shadow_proposed_commit_order` holds greedy baseline for comparison

When `primary_mode is SelectionMode.GREEDY_REGRET` (PR-GA-1): keep existing behavior.

Remove the `if not config.observe_only: raise ValueError` block in shadow builder.

- [ ] **Step 3: Pass `primary_mode` from pipeline**

In `_append_ga_evolution_shadow_step`, add `selection_mode: SelectionMode` parameter; pass to `build_ga_evolution_shadow_summary(..., primary_mode=selection_mode)`.

Update step title/summary when evolution primary:

```python
title = (
    "GA evolution shadow (greedy baseline)"
    if selection_mode is SelectionMode.EVOLUTION
    else "GA evolution shadow (observe-only)"
)
```

- [ ] **Step 4: Run shadow + PR-GA-2 tests — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_ga_evolution_shadow.py tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py -v --tb=short
```

---

## Task 6: Replay / algorithm step summary contract

**Files:**

- Modify: `django_apps/asteroid_lab/optimization/selection/ga_evolution_shadow.py` (`ga_evolution_shadow_metrics`)
- Test: `tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py`

- [ ] **Step 1: Add metrics contract test**

```python
def test_ga_shadow_metrics_include_primary_selection_mode(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    # build summary with primary_mode=EVOLUTION on toy pool (reuse shadow tests setup)
    ...
    metrics = ga_evolution_shadow_metrics(summary)
    assert metrics.get("primary_selection_mode") in ("greedy_regret", "evolution")
```

- [ ] **Step 2: Emit `primary_selection_mode` in metrics dict**

In `ga_evolution_shadow_metrics`, add:

```python
"primary_selection_mode": primary_mode.value,  # thread from summary dataclass or parameter
```

Extend `GaEvolutionShadowSummary` with optional `primary_selection_mode: str = "greedy_regret"` **only if** needed for persistence contract — prefer adding field to summary dataclass in `contracts/ga_evolution_shadow.py` (frozen dataclass — add with default for backward compat in tests).

- [ ] **Step 3: Assert selection step + shadow step both expose mode on pipeline run**

```python
def test_evolution_mode_algorithm_steps_expose_selection_mode(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(..., pipeline_config=RttpPipelineConfig(
        selection_mode=SelectionMode.EVOLUTION,
        ga_evolution_shadow=GaEvolutionShadowConfig(enabled=True, random_seed=1, generations=1),
    ))
    sel = next(r for r in result.algorithm_steps if r["step_id"] == RttpAlgorithmStepId.RTTP_GENOME_SELECTION.value)
    shadow = next(r for r in result.algorithm_steps if r["step_id"] == RttpAlgorithmStepId.RTTP_GA_EVOLUTION_SHADOW.value)
    assert sel["metrics"]["selection_mode"] == "evolution"
    assert shadow["metrics"]["primary_selection_mode"] == "evolution"
```

- [ ] **Step 4: Run — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py -k "algorithm_steps_expose or ga_shadow_metrics" -v --tb=short
```

---

## Task 7: Ops smoke (real slug)

**Files:**

- Modify: `django_apps/asteroid_lab/management/commands/run_solver.py`
- Modify: `scripts/run_solver.ps1` (if repo uses it for ops)
- Modify: `tests/unit/asteroid_lab/test_run_solver_management_command.py`

- [ ] **Step 1: Write failing CLI test**

```python
from django_apps.asteroid_lab.services.solver_run_config_keys import SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY

@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_selection_mode_evolution_sets_config() -> None:
    proj = m.AsteroidProject.objects.create(name="CliGa2", slug="cli-run-ga2-evolution")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    out = StringIO()
    with pytest.raises(SystemExit):
        call_command(
            "run_solver",
            slug=proj.slug,
            selection_mode="evolution",
            no_replay=True,
            stdout=out,
            stderr=StringIO(),
        )
    run = m.SolverRun.objects.filter(project_id=proj.pk).order_by("-id").first()
    assert run is not None
    selection = (run.config_json or {}).get(SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY) or {}
    assert selection.get("mode") == "evolution"
```

- [ ] **Step 2: Add CLI flag**

In `run_solver.py` `add_arguments`:

```python
parser.add_argument(
    "--selection-mode",
    choices=("greedy_regret", "evolution"),
    default=None,
    help="Set config_json selection.mode (PR-GA-2 normative ops entrypoint).",
)
```

In `handle`, reject combination with `--macro-only`:

```python
if options["macro_only"] and options.get("selection_mode") == "evolution":
    raise CommandError("Cannot combine --macro-only with --selection-mode=evolution.")
```

When `selection_mode` set:

```python
config[SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY] = {"mode": options["selection_mode"]}
# Ops normative: also enable GA params for evolution primary
if options["selection_mode"] == "evolution":
    config[SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY] = {
        "enabled": True,
        "generations": 4,
        "population_size": 24,
        "random_seed": 0,
    }
```

- [ ] **Step 3: Run CLI test — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_run_solver_management_command.py -k "selection_mode" -v --tb=short
```

- [ ] **Step 4: Real-map ops smoke (manual evidence for governance)**

```powershell
python manage.py run_solver --slug copy-import-495e552c --selection-mode evolution --no-replay
```

**Readback (shell):**

```python
python manage.py shell -c "
from django_apps.asteroid_lab import models as m
run = m.SolverRun.objects.filter(project__slug='copy-import-495e552c').order_by('-id').first()
ss = (run.config_json or {}).get('solver_summary') or {}
steps = ss.get('algorithm_steps') or []
sel = next(s for s in steps if s.get('step_id')=='rttp.genome_selection')
sh = next((s for s in steps if s.get('step_id')=='rttp.ga_evolution_shadow'), None)
print('selection_mode', (run.config_json or {}).get('selection'))
print('sel_metrics', sel.get('metrics'))
print('shadow_metrics', (sh or {}).get('metrics'))
print('validation_passed', ss.get('validation_passed'))
print('issue_codes', ss.get('issue_codes'))
"
```

**Expected (informational, not a hard gate on commit count):**

- `selection.mode` == `evolution` in persisted `config_json`
- `sel_metrics.selection_mode` == `evolution`
- `validation_passed` is true (same class as other ops smokes on this slug)
- `issue_codes` == `[]`
- Commit step present after selection

Record `solver_run_id` in PR description and Task 9 governance.

---

## Task 8: Regression gates

**Files:** none (verification)

- [ ] **Step 1: PR-GA-2 narrow**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py tests/unit/asteroid_lab/test_ga_evolution_shadow.py -v --tb=short
python -m pytest tests/unit/architecture/test_ga_evolution_no_probe_route.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/contracts/selection_mode.py django_apps/asteroid_lab/contracts/ga_evolution_shadow.py django_apps/asteroid_lab/optimization/selection/primary_genome.py django_apps/asteroid_lab/optimization/selection/ga_evolution_shadow.py django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/asteroid_lab/management/commands/run_solver.py tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py
```

- [ ] **Step 2: RTTP narrow regression**

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
```

Expected: PASS; count >= Task 0 baseline.

- [ ] **Step 3: Standing gates (unchanged owners)**

```powershell
powershell -File scripts/test_capacity_sot.ps1
powershell -File scripts/test_reconstruction_narrow.ps1
powershell -File scripts/test_optimization_contamination.ps1
```

- [ ] **Step 4: Full gate before PR (agent-owned per AGENTS.md)**

```powershell
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m mypy django_apps config src
python -m black --check .
```

---

## Task 9: Governance CLOSED update

**Files:**

- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/specs/2026-05-29-rttp-ga-evolution-design.md` (status)
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`
- Modify: [`2026-05-29-rttp-ga-evolution.md`](2026-05-29-rttp-ga-evolution.md) — add pointer to this plan under Appendix A

- [ ] **Step 1: After PR merge, update `current_plan.md`**

Replace ACTIVE PR-GA-2 block with:

```text
**CLOSED (YYYY-MM-DD):** RTTP GA evolution **PR-GA-2** — config-gated selection.mode (evolution primary) — PR #NN (sha).
Plan: docs/superpowers/plans/2026-05-29-rttp-ga-evolution-pr-ga-2.md
```

Move next focus to v0.1 track selection (macro child-pool spec / Lab UX defer) per queue rules.

- [ ] **Step 2: Design spec status**

In `2026-05-29-rttp-ga-evolution-design.md` header:

```text
**Status:** PR-GA-1 CLOSED (#95); PR-GA-2 CLOSED (#NN, date)
```

- [ ] **Step 3: Roadmap Axis A**

```text
PR-GA-2 selection.mode CLOSED (#NN). Next: macro child-pool fixture spec OR Lab UX defer (explicit ACTIVE row).
```

---

## Plan self-review

| Spec § | Task |
|--------|------|
| §2 forbidden boundaries | Tasks 3–4, 8 (arch test) |
| §5 PR-GA-2 scope | Tasks 1–7 |
| §7 PR-GA-2 tests | Tasks 4, 6, 8 |
| §9 governance | Task 9 |
| C-GATE fitness input boundary | Unchanged — complete-map SoT |

**Placeholder scan:** No TBD steps. Toy factories: import from `test_ga_evolution_shadow` or duplicate `_bundle_candidate` in `test_rttp_ga_evolution_pr_ga_2.py`.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-29-rttp-ga-evolution-pr-ga-2.md`.

**Do not start implementation until this plan is approved.**

**Execution options after approval:**

1. **Subagent-Driven (recommended)** — one task per subagent; review after Tasks 3, 5, and 7 checkpoints  
2. **Inline Execution** — `executing-plans` with checkpoints after Tasks 4, 7, and 8  

Which approach?
