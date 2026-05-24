# Deferred Commit Retry PR-2 Runtime Policy Implementation Plan

**Status:** CLOSED 2026-05-24 — merged `a5cfca87` (PR #73); head `1f50fc3c`; CI `ci` + `rttp-lab-macro-smoke` success.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire `SolverRun.config_json["deferred_retry_shadow"]` into `RttpPipelineConfig.deferred_retry_shadow` with strict observe-only guards and stable disabled shadow metrics — no retry execution.

**Architecture:** Pure mapper `_deferred_retry_shadow_config_from_run_config` in `solver_runtime_entry.py` extends `_rttp_pipeline_config_from_run_config`. Pipeline keeps always calling `_append_deferred_retry_shadow_step`; PR-1 builder already emits empty summary when `enabled=False` (choice B). Fail-closed on `observe_only=false` and non-bool `enabled`.

**Tech Stack:** Python 3.12+, dataclasses, Django asteroid_lab services, pytest, ruff, black

**Spec:** [`docs/superpowers/specs/2026-05-24-deferred-commit-retry-pr2-policy-design.md`](../specs/2026-05-24-deferred-commit-retry-pr2-policy-design.md)

**Branch:** `feat/deferred-commit-retry-pr2-policy` (from `master` @ `3d531407`)

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `django_apps/asteroid_lab/services/solver_run_config_keys.py` | Stable wire key constant |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Mapper + `_rttp_pipeline_config_from_run_config` |
| Modify | `django_apps/asteroid_lab/contracts/deferred_retry_shadow.py` | Docstring: wired from runtime in PR-2 |
| Create | `tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py` | Runtime + pipeline disabled contract tests |
| Modify | `tests/unit/asteroid_lab/test_rttp_db_macro_integration.py` | Assert macro mapping still works with shadow key present |
| Modify | `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | PR-2 row when done |

**No change required PR-2:** `optimization/pipeline.py` loop body (choice B — builder handles `enabled=False`). **No change:** `incremental_commit.py`, `local_lns.py`, macro pipeline.

---

### Task 0: Baseline (BLOCK if red)

**Files:** none

- [ ] **Step 1: Confirm branch**

```powershell
git checkout feat/deferred-commit-retry-pr2-policy
git merge-base --is-ancestor 1e021f20 HEAD
```

Expected: exit code 0 (PR-1 merge on ancestor chain).

- [ ] **Step 2: Narrow RTTP gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py -v --tb=short
```

Expected: all PASS.

---

### Task 1: Config key + mapper

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_config_keys.py`
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Test: `tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py`

- [ ] **Step 1: Write failing mapper tests**

Create `tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py`:

```python
"""PR-2 — runtime deferred_retry_shadow policy wiring."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.deferred_retry_shadow import DeferredRetryShadowConfig
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY,
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
    SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    _deferred_retry_shadow_config_from_run_config,
    _rttp_pipeline_config_from_run_config,
)


def test_deferred_retry_shadow_config_key_constant() -> None:
    assert SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY == "deferred_retry_shadow"


def test_absent_key_uses_defaults() -> None:
    cfg = _deferred_retry_shadow_config_from_run_config({})
    assert cfg == DeferredRetryShadowConfig()


def test_enabled_false_maps_to_disabled_config() -> None:
    cfg = _deferred_retry_shadow_config_from_run_config(
        {SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {"enabled": False}}
    )
    assert cfg.enabled is False
    assert cfg.observe_only is True
    assert cfg.max_retry_rounds == 1


def test_enabled_true_with_overrides() -> None:
    cfg = _deferred_retry_shadow_config_from_run_config(
        {
            SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {
                "enabled": True,
                "max_retry_rounds": 2,
                "max_candidates": 8,
                "route_probe_max_expansions": 250,
            }
        }
    )
    assert cfg.enabled is True
    assert cfg.max_retry_rounds == 2
    assert cfg.max_candidates == 8
    assert cfg.route_probe_max_expansions == 250


def test_observe_only_false_raises() -> None:
    with pytest.raises(ValueError, match="observe_only"):
        _deferred_retry_shadow_config_from_run_config(
            {
                SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {
                    "enabled": True,
                    "observe_only": False,
                }
            }
        )


def test_enabled_string_false_raises() -> None:
    with pytest.raises(ValueError, match="enabled"):
        _deferred_retry_shadow_config_from_run_config(
            {
                SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {
                    "enabled": "false",
                }
            }
        )


def test_non_dict_shadow_value_raises() -> None:
    with pytest.raises(ValueError, match="deferred_retry_shadow"):
        _deferred_retry_shadow_config_from_run_config(
            {SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: "off"}
        )


def test_pipeline_config_includes_shadow_and_preserves_macro() -> None:
    cfg = _rttp_pipeline_config_from_run_config(
        {
            SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY: True,
            SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY: 32,
            SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {"enabled": False},
        }
    )
    assert cfg.macro_only_mode is True
    assert cfg.max_macro_candidates == 32
    assert cfg.deferred_retry_shadow.enabled is False


def test_solver_summary_does_not_drive_shadow_config() -> None:
    cfg = _rttp_pipeline_config_from_run_config(
        {
            "solver_summary": {
                "algorithm_steps": [
                    {
                        "step_id": "rttp.deferred_commit_retry_shadow",
                        "metrics": {"enabled": False, "candidate_count": 99},
                    }
                ]
            },
            SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {"enabled": True},
        }
    )
    assert cfg.deferred_retry_shadow.enabled is True
```

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py -v --tb=short
```

Expected: FAIL (`_deferred_retry_shadow_config_from_run_config` not defined).

- [ ] **Step 3: Add config key**

In `django_apps/asteroid_lab/services/solver_run_config_keys.py`:

```python
SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY = "deferred_retry_shadow"
```

Add to `__all__` list (alphabetically with other RTTP keys).

- [ ] **Step 4: Implement mapper in solver_runtime_entry.py**

Add imports:

```python
from django_apps.asteroid_lab.contracts.deferred_retry_shadow import DeferredRetryShadowConfig
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    ...
    SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY,
)
```

Add helper **before** `_rttp_pipeline_config_from_run_config`:

```python
def _require_bool(value: object, *, field: str) -> bool:
    if isinstance(value, bool):
        return value
    msg = f"deferred_retry_shadow.{field} must be a boolean"
    raise ValueError(msg)


def _deferred_retry_shadow_config_from_run_config(
    config: dict[str, Any],
) -> DeferredRetryShadowConfig:
    """Map ``config_json`` shadow policy (PR-2); never reads solver_summary."""

    raw = config.get(SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY)
    if raw is None:
        return DeferredRetryShadowConfig()
    if not isinstance(raw, dict):
        msg = "deferred_retry_shadow must be an object"
        raise ValueError(msg)
    if "observe_only" in raw:
        if not _require_bool(raw["observe_only"], field="observe_only"):
            msg = "deferred_retry_shadow.observe_only must remain true in PR-2"
            raise ValueError(msg)
    enabled = _require_bool(raw.get("enabled", True), field="enabled")
    max_rounds_raw = raw.get("max_retry_rounds", 1)
    if not isinstance(max_rounds_raw, int):
        msg = "deferred_retry_shadow.max_retry_rounds must be an integer"
        raise ValueError(msg)
    max_candidates_raw = raw.get("max_candidates")
    max_candidates: int | None
    if max_candidates_raw is None:
        max_candidates = None
    elif isinstance(max_candidates_raw, int):
        max_candidates = max_candidates_raw
    else:
        msg = "deferred_retry_shadow.max_candidates must be an integer or null"
        raise ValueError(msg)
    expansions_raw = raw.get("route_probe_max_expansions", 500)
    if not isinstance(expansions_raw, int):
        msg = "deferred_retry_shadow.route_probe_max_expansions must be an integer"
        raise ValueError(msg)
    return DeferredRetryShadowConfig(
        enabled=enabled,
        observe_only=True,
        max_retry_rounds=max_rounds_raw,
        max_candidates=max_candidates,
        route_probe_max_expansions=expansions_raw,
    )
```

Update `_rttp_pipeline_config_from_run_config`:

```python
def _rttp_pipeline_config_from_run_config(config: dict[str, Any]) -> RttpPipelineConfig:
    macro_only = bool(config.get(SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY, False))
    max_raw = config.get(SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY, 64)
    max_macro = int(max_raw) if max_raw is not None else 64
    shadow = _deferred_retry_shadow_config_from_run_config(config)
    return RttpPipelineConfig(
        macro_only_mode=macro_only,
        max_macro_candidates=max_macro,
        deferred_retry_shadow=shadow,
    )
```

Export `_deferred_retry_shadow_config_from_run_config` in module `__all__` if the file has one; tests import it directly (same pattern as macro tests).

- [ ] **Step 5: Run mapper tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py -v --tb=short
```

Expected: PASS (mapper tests only; pipeline tests in Task 2).

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/services/solver_run_config_keys.py django_apps/asteroid_lab/services/solver_runtime_entry.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py
git commit -m "feat(asteroid-lab): wire deferred_retry_shadow from run config"
```

---

### Task 2: Pipeline disabled behavior tests

**Files:**
- Modify: `tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py`
- Modify: `django_apps/asteroid_lab/contracts/deferred_retry_shadow.py` (docstring only)

- [ ] **Step 1: Add pipeline disabled tests**

Append to `test_deferred_commit_retry_pr2_policy.py`:

```python
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.rttp_solver_summary import (
    RttpAlgorithmStepId,
)


def test_disabled_shadow_step_present_with_empty_metrics(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    result = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            deferred_retry_shadow=DeferredRetryShadowConfig(enabled=False),
        ),
    )
    shadow = next(
        row
        for row in result.algorithm_steps
        if row["step_id"]
        == RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value
    )
    assert shadow["passed"] is True
    assert shadow["metrics"]["enabled"] is False
    assert shadow["metrics"]["observe_only"] is True
    assert shadow["metrics"]["candidate_count"] == 0
    assert shadow["metrics"]["eligible_candidate_ids"] == []


def test_disabled_shadow_does_not_change_commit_or_validation(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    baseline = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            deferred_retry_shadow=DeferredRetryShadowConfig(),
        ),
    )
    disabled = run_rttp_pipeline(
        greenfield_optimization_input,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        pipeline_config=RttpPipelineConfig(
            deferred_retry_shadow=DeferredRetryShadowConfig(enabled=False),
        ),
    )
    assert disabled.commit_result.committed_ids == baseline.commit_result.committed_ids
    assert disabled.commit_result.conflicts == baseline.commit_result.conflicts
    assert disabled.validation_passed == baseline.validation_passed
    assert disabled.genome.commit_order == baseline.genome.commit_order
```

- [ ] **Step 2: Run pipeline tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py -v --tb=short
```

Expected: all PASS.

- [ ] **Step 3: Update contract docstring**

In `django_apps/asteroid_lab/contracts/deferred_retry_shadow.py`, change `DeferredRetryShadowConfig` docstring to:

```python
    """Runtime shadow policy; wired from SolverRun.config_json in PR-2."""
```

- [ ] **Step 4: Extend macro integration test (regression)**

In `tests/unit/asteroid_lab/test_rttp_db_macro_integration.py`, extend `test_run_config_maps_macro_only_to_pipeline_config`:

```python
    cfg = _rttp_pipeline_config_from_run_config(
        {
            SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY: True,
            SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY: 32,
            SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY: {"enabled": False},
        }
    )
    assert cfg.macro_only_mode is True
    assert cfg.max_macro_candidates == 32
    assert cfg.deferred_retry_shadow.enabled is False
```

Remove duplicate lines from old test body if replacing entire dict.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py django_apps/asteroid_lab/contracts/deferred_retry_shadow.py tests/unit/asteroid_lab/test_rttp_db_macro_integration.py
git commit -m "test(asteroid-lab): PR-2 disabled shadow and macro config regression"
```

---

### Task 3: Gates + self-review

**Files:** none (verification only)

- [ ] **Step 1: Lint and format**

```powershell
python -m ruff check django_apps/asteroid_lab/services/solver_run_config_keys.py django_apps/asteroid_lab/services/solver_runtime_entry.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py
python -m black --check django_apps/asteroid_lab/services/solver_run_config_keys.py django_apps/asteroid_lab/services/solver_runtime_entry.py tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py tests/unit/asteroid_lab/test_rttp_db_macro_integration.py
```

Expected: PASS. On black fail: `python -m black` on those paths and commit `style: ...`.

- [ ] **Step 2: Regression bundle**

```powershell
python -m pytest tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py tests/unit/asteroid_lab/test_rttp_db_macro_integration.py tests/unit/asteroid_lab/test_rttp_solver_summary.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
```

Expected: all PASS.

- [ ] **Step 3: Self-review checklist**

| INV | Check |
|-----|-------|
| INV-PR2-01 | No new probe/commit in shadow path |
| INV-PR2-02 | `observe_only=false` → ValueError |
| INV-PR2-03 | Disabled vs default greenfield parity test |
| INV-PR2-04 | Shadow step still before commit step in ordering tests |
| INV-PR2-05 | `solver_summary` in config does not affect mapper |
| INV-PR2-06 | Macro config test includes shadow key |

- [ ] **Step 4: PR body template**

```markdown
## Summary
- Wire `config_json.deferred_retry_shadow` to `RttpPipelineConfig` via strict mapper
- `enabled=false` yields empty shadow metrics; step shape stable (choice B)
- Reject `observe_only=false` and non-bool `enabled` (PR-2 fail-closed)

## Test plan
- [x] test_deferred_commit_retry_pr2_policy.py
- [x] test_deferred_commit_retry_shadow.py
- [x] RTTP narrow gate
- [x] contamination gate
```

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| Wire key `deferred_retry_shadow` | Task 1 Step 3 |
| Mapper table (absent / false / overrides / reject) | Task 1 Step 4 + tests |
| Choice B disabled behavior | Task 2 (builder; no pipeline edit) |
| observe_only guard | Task 1 tests + mapper |
| No execution invariants | Task 3 checklist |
| Macro unaffected | Task 2 Step 4 |
| Verification commands | Task 3 |

No TBD placeholders in task code blocks.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-24-deferred-commit-retry-pr2-policy.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task + spec/quality review  
2. **Inline Execution** — this session with `executing-plans` checkpoints

Which approach?
