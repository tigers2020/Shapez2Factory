# RTTP GA Evolution — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add observe-only GA evolution shadow (PR-GA-1) after greedy genome selection; greedy remains commit authority. PR-GA-2 (config `selection.mode` swap) is a separate follow-up.

**Architecture:** `GaEvolutionShadowConfig` + pure `run_ga_evolution_shadow` produce `GaEvolutionShadowSummary`; pipeline appends `rttp.ga_evolution_shadow` step before commit without changing `PlacementGenome` passed to `incremental_commit`. Fitness in `genome_fitness.py` reuses greedy base-score semantics on candidate-phase fields only.

**Tech Stack:** Python 3.12+, dataclasses, pytest, ruff, black, mypy `django_apps config src`

**Spec:** [`../specs/2026-05-29-rttp-ga-evolution-design.md`](../specs/2026-05-29-rttp-ga-evolution-design.md)

**Branch:** `feat/rttp-ga-evolution-shadow` (dedicated worktree recommended)

---

## File map (PR-GA-1 only)

| File | Action | Responsibility |
|------|--------|----------------|
| `django_apps/asteroid_lab/contracts/ga_evolution_shadow.py` | Create | Config + summary DTOs |
| `django_apps/asteroid_lab/optimization/selection/genome_fitness.py` | Create | Validity + fitness (probe-time only) |
| `django_apps/asteroid_lab/optimization/selection/ga_evolution.py` | Create | Bounded GA operators + `select_genome_evolution` |
| `django_apps/asteroid_lab/optimization/selection/ga_evolution_shadow.py` | Create | Summary builder + metrics projection |
| `django_apps/asteroid_lab/optimization/pipeline.py` | Modify | Shadow step after selection, before commit |
| `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | Modify | `RTTP_GA_EVOLUTION_SHADOW` step id |
| `django_apps/asteroid_lab/replay/event_types.py` | Modify | `EVENT_TYPE_RTTP_GA_EVOLUTION_SHADOW` |
| `django_apps/asteroid_lab/optimization/input_contracts.py` | Modify | `ga_evolution_shadow` on `RttpPipelineConfig` |
| `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Modify | `config_json` mapper |
| `tests/unit/asteroid_lab/test_ga_evolution_shadow.py` | Create | Unit + pipeline hook tests |
| `documents/ai/current_plan.md` | Modify | PR-GA-1 ACTIVE row |

**PR-GA-2 (out of scope here):** `selection_mode` enum, pipeline branch, production `select_genome_evolution` default path — see Appendix A.

---

## Task 0: Preflight

**Files:** none

- [ ] **Step 1: Confirm C-GATE green on `master`**

```powershell
git checkout master
git pull origin master
powershell -File scripts/test_capacity_sot.ps1
```

Expected: exit 0

- [ ] **Step 2: Baseline RTTP narrow**

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
```

Expected: PASS (record count for regression)

- [ ] **Step 3: Create branch**

```powershell
git checkout -b feat/rttp-ga-evolution-shadow
```

---

## Task 1: Contracts (`GaEvolutionShadowConfig` / `Summary`)

**Files:**

- Create: `django_apps/asteroid_lab/contracts/ga_evolution_shadow.py`
- Test: `tests/unit/asteroid_lab/test_ga_evolution_shadow.py` (start file)

- [ ] **Step 1: Write failing contract test**

Add to `tests/unit/asteroid_lab/test_ga_evolution_shadow.py`:

```python
"""PR-GA-1 — GA evolution observe-only shadow."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.ga_evolution_shadow import (
    GaEvolutionShadowConfig,
    GaEvolutionShadowSummary,
)


def test_ga_shadow_config_defaults_disabled() -> None:
    cfg = GaEvolutionShadowConfig()
    assert cfg.enabled is False
    assert cfg.observe_only is True
    assert cfg.population_size == 24
    assert cfg.generations == 8


def test_ga_shadow_summary_frozen() -> None:
    summary = GaEvolutionShadowSummary(
        enabled=True,
        observe_only=True,
        primary_commit_order=("a",),
        shadow_proposed_commit_order=("b",),
        shadow_fitness_total=1.0,
        generations_run=1,
        population_size=24,
        overlap_violation_count=0,
        gene_count=1,
        anchor_count=1,
        order_agreement_ratio=0.0,
    )
    assert summary.enabled is True
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_ga_evolution_shadow.py::test_ga_shadow_config_defaults_disabled -v --tb=short
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement contracts**

Create `django_apps/asteroid_lab/contracts/ga_evolution_shadow.py`:

```python
"""GA evolution shadow contracts (PR-GA-1 observe-only)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GaEvolutionShadowConfig:
    enabled: bool = False
    observe_only: bool = True
    population_size: int = 24
    generations: int = 8
    mutation_rate: float = 0.15
    tournament_size: int = 3
    elite_count: int = 2
    random_seed: int = 0


@dataclass(frozen=True, slots=True)
class GaEvolutionShadowSummary:
    enabled: bool
    observe_only: bool
    primary_commit_order: tuple[str, ...]
    shadow_proposed_commit_order: tuple[str, ...]
    shadow_fitness_total: float
    generations_run: int
    population_size: int
    overlap_violation_count: int
    gene_count: int
    anchor_count: int
    order_agreement_ratio: float


__all__ = ["GaEvolutionShadowConfig", "GaEvolutionShadowSummary"]
```

- [ ] **Step 4: Run contract tests — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_ga_evolution_shadow.py -k "ga_shadow_config or ga_shadow_summary" -v --tb=short
```

---

## Task 2: Genome fitness (shared scoring)

**Files:**

- Create: `django_apps/asteroid_lab/optimization/selection/genome_fitness.py`
- Test: `tests/unit/asteroid_lab/test_ga_evolution_shadow.py`

- [ ] **Step 1: Failing fitness test on toy candidates**

Append imports and test (use existing RTTP test helpers if available, else minimal `BundleCandidate` factory from `test_rttp_commit` patterns):

```python
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput, TransportKind
from django_apps.asteroid_lab.optimization.selection.genome_fitness import (
    evaluate_genome_fitness,
    genome_layout_valid,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import SelectionConfig
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def _toy_candidate(cid: str, x: int, y: int, *, tf: int = 8) -> BundleCandidate:
    # Match fields required by genome_fitness; copy from test_rttp_narrow_corridor or conftest.
    ...


def test_overlapping_genome_invalid_fitness() -> None:
    # Two candidates with overlapping occupied_cells → genome_layout_valid False
    ...
```

Implement minimal toy factory by reading `tests/unit/asteroid_lab/conftest.py` RTTP helpers — **do not** invent divergent `BundleCandidate` shapes.

- [ ] **Step 2: Implement `genome_fitness.py`**

Key functions:

```python
def genome_layout_valid(
    commit_order: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
    *,
    goal_count: int,
) -> bool:
    """Disjoint occupied + FOT layout; length <= goal_count."""


def evaluate_genome_fitness(
    commit_order: Sequence[str],
    *,
    candidates_by_id: Mapping[str, BundleCandidate],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    config: SelectionConfig | None = None,
) -> float:
    """Sum greedy base_score along build order; -inf if invalid."""
```

Import `_base_score`, `_overlaps`, `_fot_conflict`, `fixed_output_transport_cell` from `greedy_regret` / `placement_cells` — **do not** duplicate coefficient constants in a second place; import private helpers only within `optimization/selection/` package (same subtree as PR-B allowlist).

- [ ] **Step 3: Run fitness tests — PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_ga_evolution_shadow.py -k "overlapping_genome" -v --tb=short
```

---

## Task 3: Bounded GA core

**Files:**

- Create: `django_apps/asteroid_lab/optimization/selection/ga_evolution.py`
- Test: `tests/unit/asteroid_lab/test_ga_evolution_shadow.py`

- [ ] **Step 1: Failing test — evolution returns genome ≤ goal_count**

```python
from django_apps.asteroid_lab.optimization.selection.ga_evolution import select_genome_evolution
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome


def test_select_genome_evolution_respects_goal_count() -> None:
    # 4 candidates, goal_count=2 → len(commit_order) <= 2
    genome = select_genome_evolution(pool, skeleton, inp, goal_count=2, config=ga_cfg)
    assert isinstance(genome, PlacementGenome)
    assert len(genome.commit_order) <= 2
```

- [ ] **Step 2: Implement `select_genome_evolution`**

```python
def select_genome_evolution(
    normal_candidates: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    *,
    goal_count: int,
    config: GaEvolutionShadowConfig,
    selection_config: SelectionConfig | None = None,
) -> PlacementGenome:
    """Bounded GA; deterministic with config.random_seed."""
```

Algorithm (YAGNI v0):

1. `dedupe_candidates` pool
2. Seed RNG with `config.random_seed`
3. Initialize population with random valid genomes (greedy-build valid sequences)
4. For `generations` iterations: tournament select → order crossover → mutation (swap/add/remove)
5. Track best fitness; return `PlacementGenome(commit_order=best)`

- [ ] **Step 3: Run test — PASS**

---

## Task 4: Shadow summary + metrics

**Files:**

- Create: `django_apps/asteroid_lab/optimization/selection/ga_evolution_shadow.py`
- Test: `tests/unit/asteroid_lab/test_ga_evolution_shadow.py`

- [ ] **Step 1: Failing test — disabled shadow empty proposal**

```python
from django_apps.asteroid_lab.optimization.selection.ga_evolution_shadow import (
    build_ga_evolution_shadow_summary,
    ga_evolution_shadow_metrics,
)


def test_shadow_disabled_returns_empty_proposal() -> None:
    summary = build_ga_evolution_shadow_summary(
        primary_genome=PlacementGenome(commit_order=("c1",)),
        normal_candidates=(),
        skeleton=skeleton,
        inp=inp,
        goal_count=1,
        config=GaEvolutionShadowConfig(enabled=False),
    )
    assert summary.enabled is False
    assert summary.shadow_proposed_commit_order == ()
```

- [ ] **Step 2: Implement shadow builder**

```python
def build_ga_evolution_shadow_summary(
    *,
    primary_genome: PlacementGenome,
    normal_candidates: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goal_count: int,
    config: GaEvolutionShadowConfig,
) -> GaEvolutionShadowSummary:
    if not config.enabled:
        return GaEvolutionShadowSummary(enabled=False, observe_only=True, ...)
    assert config.observe_only is True
    shadow_genome = select_genome_evolution(..., config=config)
    # compute order_agreement_ratio, anchor_count, etc.
```

```python
def ga_evolution_shadow_metrics(summary: GaEvolutionShadowSummary) -> dict[str, Any]:
    """JSON-serializable metrics for algorithm_steps."""
```

- [ ] **Step 3: Enabled shadow produces proposal on toy pool — PASS**

---

## Task 5: Pipeline integration

**Files:**

- Modify: `django_apps/asteroid_lab/optimization/rttp_solver_summary.py`
- Modify: `django_apps/asteroid_lab/replay/event_types.py`
- Modify: `django_apps/asteroid_lab/optimization/input_contracts.py`
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py`
- Test: `tests/unit/asteroid_lab/test_ga_evolution_shadow.py`

- [ ] **Step 1: Add step id and event type**

In `rttp_solver_summary.py`:

```python
    RTTP_GA_EVOLUTION_SHADOW = "rttp.ga_evolution_shadow"
```

In `replay/event_types.py`:

```python
EVENT_TYPE_RTTP_GA_EVOLUTION_SHADOW = "rttp.ga_evolution_shadow"
```

Add to `RTTP_EVENT_TYPES` frozenset if present.

- [ ] **Step 2: Extend `RttpPipelineConfig`**

In `input_contracts.py`:

```python
from django_apps.asteroid_lab.contracts.ga_evolution_shadow import GaEvolutionShadowConfig

@dataclass(frozen=True, slots=True)
class RttpPipelineConfig:
    ...
    ga_evolution_shadow: GaEvolutionShadowConfig = field(
        default_factory=GaEvolutionShadowConfig
    )
```

- [ ] **Step 3: Add `_append_ga_evolution_shadow_step` in `pipeline.py`**

Mirror `_append_deferred_retry_shadow_step`:

```python
def _append_ga_evolution_shadow_step(
    steps: list[dict[str, Any]],
    *,
    shadow_config: GaEvolutionShadowConfig,
    primary_genome: PlacementGenome,
    normal_candidates: tuple[BundleCandidate, ...],
    skeleton: RttpSkeleton,
    inp: OptimizationInput,
    goal_count: int,
) -> None:
    summary = build_ga_evolution_shadow_summary(...)
    metrics = ga_evolution_shadow_metrics(summary)
    steps.append(
        algorithm_step_summary_to_json(
            {
                "step_id": RttpAlgorithmStepId.RTTP_GA_EVOLUTION_SHADOW.value,
                "phase": "genome_fitness",
                "event_type": "rttp.ga_evolution_shadow",
                "title": "GA evolution shadow (observe-only)",
                "summary": "Parallel GA proposal; greedy genome remains commit authority.",
                "metrics": metrics,
                "passed": True,
            }
        )
    )
```

Call site in `run_rttp_pipeline` **after** selection step, **before** `_append_deferred_retry_shadow_step` / `incremental_commit`:

```python
    genome = select_genome(...)
    ...
    _append_ga_evolution_shadow_step(
        steps,
        shadow_config=config.ga_evolution_shadow,
        primary_genome=genome,
        normal_candidates=generation.normal_candidates,
        skeleton=skeleton,
        inp=inp,
        goal_count=selection_goal,
    )
    primary_commit_result = incremental_commit(genome, ...)  # unchanged
```

- [ ] **Step 4: Test — pipeline records step when enabled**

Use monkeypatch on `build_ga_evolution_shadow_summary` or run small pipeline slice test asserting step_id in `steps` list.

- [ ] **Step 5: Test — commit still uses greedy genome**

Assert `incremental_commit` call receives same `genome` object/order as greedy output (mock/spy).

---

## Task 6: Runtime config mapper

**Files:**

- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Test: `tests/unit/asteroid_lab/test_ga_evolution_shadow.py` or extend `test_deferred_commit_retry_pr2_policy.py` pattern

- [ ] **Step 1: Failing mapper test**

```python
def test_ga_shadow_config_from_run_config_enabled() -> None:
    cfg = _ga_evolution_shadow_config_from_run_config(
        {"ga_evolution_shadow": {"enabled": True, "generations": 4}}
    )
    assert cfg.enabled is True
    assert cfg.generations == 4
    assert cfg.observe_only is True
```

- [ ] **Step 2: Implement `_ga_evolution_shadow_config_from_run_config`**

Fail-closed: bool fields must be bool; ints must be int; reject `observe_only: false` in PR-GA-1 with `ValueError` (PR-GA-2 opens this).

Wire into `_rttp_pipeline_config_from_run_config` alongside `deferred_retry_shadow`.

- [ ] **Step 3: Run mapper tests — PASS**

---

## Task 7: Architecture guard (no probe in GA modules)

**Files:**

- Create or extend: `tests/unit/architecture/test_ga_evolution_no_probe_route.py` (optional small file)

- [ ] **Step 1: AST test — ga_evolution*.py must not import routing probe**

```python
_FORBIDDEN = ("probe_route", "route_probe")
_GA_ROOT = _LAB_ROOT / "optimization" / "selection"
```

Scan `ga_evolution.py`, `ga_evolution_shadow.py`, `genome_fitness.py` only.

- [ ] **Step 2: Run — PASS**

```powershell
python -m pytest tests/unit/architecture/test_ga_evolution_no_probe_route.py -v --tb=short
```

---

## Task 8: Governance

**Files:**

- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` (one line under Axis A)

- [ ] **Step 1: Update `current_plan` Next focus**

```markdown
**ACTIVE:** RTTP GA evolution PR-GA-1 — observe-only shadow
- Spec: docs/superpowers/specs/2026-05-29-rttp-ga-evolution-design.md
- Plan: docs/superpowers/plans/2026-05-29-rttp-ga-evolution.md
- Blocks: PR-GA-2 selection.mode swap until PR-GA-1 CLOSED
```

Keep existing GA line as sub-bullet or replace v0.1 GA ACTIVE with PR-GA-1 specific text.

- [ ] **Step 2: Roadmap Axis A pointer**

```text
ACTIVE: PR-GA-1 GA shadow (spec 2026-05-29); PR-GA-2 evolution mode after CLOSED
```

---

## Task 9: Narrow verification

- [ ] **Step 1: GA tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_ga_evolution_shadow.py -v --tb=short
```

- [ ] **Step 2: RTTP regression (default config — shadow off)**

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
```

- [ ] **Step 3: Ruff + black**

```powershell
python -m ruff check django_apps/asteroid_lab/contracts/ga_evolution_shadow.py django_apps/asteroid_lab/optimization/selection/genome_fitness.py django_apps/asteroid_lab/optimization/selection/ga_evolution.py django_apps/asteroid_lab/optimization/selection/ga_evolution_shadow.py django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/services/solver_runtime_entry.py tests/unit/asteroid_lab/test_ga_evolution_shadow.py
python -m black --check django_apps/asteroid_lab/contracts/ga_evolution_shadow.py django_apps/asteroid_lab/optimization/selection/genome_fitness.py django_apps/asteroid_lab/optimization/selection/ga_evolution.py django_apps/asteroid_lab/optimization/selection/ga_evolution_shadow.py
```

- [ ] **Step 4: Standing gates**

```powershell
powershell -File scripts/test_capacity_sot.ps1
powershell -File scripts/test_optimization_contamination.ps1
```

---

## Appendix A — PR-GA-2 (config-gated swap)

**Status:** **CLOSED** (2026-05-30) — PR [#97](https://github.com/tigers2020/Shapez2Factory/pull/97) squash-merged to `master` (`e43e197b`). Executable plan: [`2026-05-29-rttp-ga-evolution-pr-ga-2.md`](2026-05-29-rttp-ga-evolution-pr-ga-2.md). Governance close: [`../specs/2026-05-30-rttp-ga-evolution-pr-ga-2-governance-close-design.md`](../specs/2026-05-30-rttp-ga-evolution-pr-ga-2-governance-close-design.md).

| Task | Work | Dedicated plan |
|------|------|----------------|
| A1 | `SelectionMode` StrEnum + `RttpPipelineConfig.selection_mode` | Task 1 |
| A2 | Pipeline branch: `select_genome_evolution` when `evolution` | Tasks 3–4 |
| A3 | Shadow policy cleanup (`observe_only` not commit switch) | Task 5 |
| A4 | `config_json.selection.mode` mapper fail-closed | Task 2 |
| A5 | Tests: default greedy unchanged; evolution primary commit spy | Task 4 |
| A6 | Ops smoke: `copy-import-495e552c` `--selection-mode evolution` | Task 7 |
| A7 | `current_plan` PR-GA-2 CLOSED | Task 9 |

---

## Plan self-review

| Spec § | Task |
|--------|------|
| §2 forbidden (no probe/generate) | Task 7, Task 2 |
| §3 PR-GA-1 shadow invariants | Task 4–5 |
| §4 contracts | Task 1, 4, 6 |
| §5 PR-GA-2 | Appendix A only |
| §7 tests | Tasks 2–7, 9 |
| §9 governance | Task 8 |

No TBD steps. Toy `BundleCandidate` factory defers to conftest — implementer must fill from existing RTTP tests in Task 2 Step 1.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-29-rttp-ga-evolution.md`.

**Spec:** `docs/superpowers/specs/2026-05-29-rttp-ga-evolution-design.md` — review alongside plan.

**Execution options:**

1. **Subagent-Driven (recommended)** — one task per subagent, review between tasks  
2. **Inline Execution** — executing-plans with checkpoint after Task 5 and Task 9  

Which approach for PR-GA-1?
