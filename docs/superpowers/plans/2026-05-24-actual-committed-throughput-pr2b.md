# PR-2b — Actual Committed Throughput Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compute `actual_committed_output_per_min` from route-confirmed committed candidates using `MiningExtractionRule.output_per_min`, persist on `solver_summary`, and show it on Lab card 5 — without target percent or budget logic (PR-2c).

**Architecture:** Pure `committed_throughput_summary` service sums rates for committed candidate IDs; `pipeline.py` computes at end of v0.1 and macro pipelines into new `PipelineResult` field; `solver_runtime_entry` passes into `build_rttp_solver_summary`; Lab DTO sets `actual_output_status=available`.

**Tech Stack:** Python 3.12, Django, `Decimal`, pytest-django, ruff, existing `django_apps/game_data/services/mining_extraction_rules.py`

**Spec:** PR-2b scope in [`2026-05-24-throughput-target-percent-pr2c-design.md`](../specs/2026-05-24-throughput-target-percent-pr2c-design.md) (PR split) · PR-2a unchanged [`2026-05-24-reconstruction-max-throughput-pr2a-design.md`](../specs/2026-05-24-reconstruction-max-throughput-pr2a-design.md)

**Branch:** `feat/asteroid-lab-committed-throughput-pr2b` (worktree recommended)

**Out of scope:** `throughput_target_percent`, `target_throughput_per_min`, `throughput_budget_satisfied` truth, UI percent slider, selection scoring

## Invariants (reviewer amendments)

```text
actual_committed_output_per_min
  = sum(route-confirmed committed physical extractor bundle outputs)

Each committed bundle is counted exactly once.
Macro parent and committed children must not both contribute throughput.
```

**Allowed:** `BundleCandidate.throughput_factor`, `transport_kind` → `resource_kind`, `MiningExtractionRule.output_per_min`, commit `committed_ids` / macro `committed_child_ids` only.

**Forbidden:** `candidate_id` parsing, `commit_order` parsing, `solver_summary` reverse-read, replay frames.

**Numeric:** `Decimal` internally; output via `decimal_str()` (4dp string). No `float`.

**Macro wire:** `CommitResult.committed_ids` for macro runs are already `committed_child_ids` (`_macro_commit_as_bundle_result`). Do not pass macro parent IDs into the sum.

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `django_apps/asteroid_lab/services/committed_throughput_summary.py` | Sum committed platform output rates |
| Create | `tests/unit/asteroid_lab/test_committed_throughput_summary.py` | Unit tests with rule fixtures |
| Modify | `django_apps/asteroid_lab/optimization/pipeline.py` | `PipelineResult.actual_committed_output_per_min` |
| Modify | `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | Optional summary key |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Wire pipeline field → summary |
| Modify | `django_apps/asteroid_lab/services/solver_run_lab_summary.py` | Card 5 uses actual when present |
| Modify | `tests/unit/asteroid_lab/test_rttp_solver_summary.py` | Summary includes actual |
| Modify | `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` | `actual_output_status` available |
| Modify | `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Card 5 subtitle `{n}/min` |
| Modify | `scripts/build_locale_ko.py` | msgid for committed throughput subtitle if new |

---

### Task 1: `resource_kind_for_transport` + committed sum (pure)

**Files:**
- Create: `django_apps/asteroid_lab/services/committed_throughput_summary.py`
- Create: `tests/unit/asteroid_lab/test_committed_throughput_summary.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/asteroid_lab/test_committed_throughput_summary.py
from decimal import Decimal

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.committed_throughput_summary import (
    build_actual_committed_output_per_min,
    resource_kind_for_transport,
)
from django_apps.game_data.services.mining_extraction_rules import get_active_rule


def _candidate(cid: str, factor: int) -> BundleCandidate:
    from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library

    pattern = next(p for p in build_pattern_library() if p.pattern_id == "lin_e_len0")
    anchor = (0, 0)
    return BundleCandidate(
        candidate_id=cid,
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=frozenset(anchor),
        output_stub=(1, 0),
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=factor,
        route_probe_cost=1,
        reachable=True,
    )


@pytest.mark.django_db
def test_actual_committed_output_does_not_double_count_macro_parent_and_children() -> None:
    child = _candidate("child-a", 16)
    rule = get_active_rule("shape")
    expected = rule.mini_unit_output_per_min * Decimal(16)
    actual = build_actual_committed_output_per_min(
        committed_ids=("macro-m1", "child-a"),
        candidates_by_id={"child-a": child},
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert actual == format(expected.quantize(Decimal("0.0001")), "f")


@pytest.mark.django_db
def test_resource_kind_for_transport_shape() -> None:
    assert resource_kind_for_transport(TransportKind.SHAPE_BELT) == "shape"


@pytest.mark.django_db
def test_build_actual_sums_committed_throughput_factors() -> None:
    rule = get_active_rule("shape")
    c1 = _candidate("a", 16)
    c2 = _candidate("b", 8)
    expected = (
        rule.mini_unit_output_per_min * Decimal(16)
        + rule.mini_unit_output_per_min * Decimal(8)
    )
    actual = build_actual_committed_output_per_min(
        committed_ids=("a", "b"),
        candidates_by_id={"a": c1, "b": c2},
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert actual == format(expected.quantize(Decimal("0.0001")), "f")


@pytest.mark.django_db
def test_build_actual_ignores_missing_candidate_id() -> None:
    c1 = _candidate("a", 4)
    actual = build_actual_committed_output_per_min(
        committed_ids=("a", "missing"),
        candidates_by_id={"a": c1},
        transport_kind=TransportKind.SHAPE_BELT,
    )
    rule = get_active_rule("shape")
    single = rule.mini_unit_output_per_min * Decimal(4)
    assert actual == format(single.quantize(Decimal("0.0001")), "f")
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_committed_throughput_summary.py -v --tb=short
```

Expected: `ModuleNotFoundError` for `committed_throughput_summary`.

- [ ] **Step 3: Implement service**

```python
# django_apps/asteroid_lab/services/committed_throughput_summary.py
"""Route-confirmed committed platform throughput (PR-2b; never replay input)."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import decimal_str
from django_apps.game_data.services.mining_extraction_rules import get_active_rule, output_per_min


def resource_kind_for_transport(transport_kind: TransportKind) -> str:
    if transport_kind is TransportKind.SHAPE_BELT:
        return "shape"
    if transport_kind is TransportKind.FLUID_PIPE:
        return "fluid"
    msg = f"unsupported transport_kind={transport_kind!r}"
    raise ValueError(msg)


def build_actual_committed_output_per_min(
    *,
    committed_ids: tuple[str, ...],
    candidates_by_id: Mapping[str, BundleCandidate],
    transport_kind: TransportKind,
) -> str:
    rule = get_active_rule(resource_kind_for_transport(transport_kind))
    total = Decimal(0)
    for cid in committed_ids:
        candidate = candidates_by_id.get(cid)
        if candidate is None:
            continue
        total += output_per_min(rule, int(candidate.throughput_factor))
    return decimal_str(total)


__all__ = [
    "build_actual_committed_output_per_min",
    "resource_kind_for_transport",
]
```

- [ ] **Step 4: Run test — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_committed_throughput_summary.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/committed_throughput_summary.py tests/unit/asteroid_lab/test_committed_throughput_summary.py
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/services/committed_throughput_summary.py tests/unit/asteroid_lab/test_committed_throughput_summary.py
git commit -m "feat(asteroid_lab): sum actual committed throughput from candidates"
```

---

### Task 2: Macro path uses `committed_child_ids`

**Files:**
- Modify: `django_apps/asteroid_lab/services/committed_throughput_summary.py`
- Modify: `tests/unit/asteroid_lab/test_committed_throughput_summary.py`

- [ ] **Step 1: Add failing macro test**

```python
def test_build_actual_macro_uses_child_ids() -> None:
    children = ("c1", "c2")
    cand = {cid: _candidate(cid, 16) for cid in children}
    actual = build_actual_committed_output_per_min(
        committed_ids=children,
        candidates_by_id=cand,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    rule = get_active_rule("shape")
    expected = rule.mini_unit_output_per_min * Decimal(16) * 2
    assert actual == format(expected.quantize(Decimal("0.0001")), "f")
```

(Document: macro pipeline passes `macro_commit.committed_child_ids`, not macro_ids.)

- [ ] **Step 2: Run — PASS (no code change if API already accepts id tuple)**

- [ ] **Step 3: Commit** (only if test file changed)

```bash
git add tests/unit/asteroid_lab/test_committed_throughput_summary.py
git commit -m "test(asteroid_lab): document macro child id throughput sum"
```

---

### Task 3: `PipelineResult` field + pipeline wire

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py` (or nearest greenfield test)

- [ ] **Step 1: Extend dataclass**

In `pipeline.py` `PipelineResult`:

```python
actual_committed_output_per_min: str | None = None
```

- [ ] **Step 2: Compute in `_run_v01_rttp_pipeline` before return**

```python
from django_apps.asteroid_lab.services.committed_throughput_summary import (
    build_actual_committed_output_per_min,
)

actual_rate = build_actual_committed_output_per_min(
    committed_ids=commit_result.committed_ids,
    candidates_by_id=candidates_by_id,
    transport_kind=inp.transport_kind,
)
return PipelineResult(
    ...
    actual_committed_output_per_min=actual_rate,
)
```

- [ ] **Step 3: Compute in `_run_macro_rttp_pipeline`**

```python
actual_rate = build_actual_committed_output_per_min(
    committed_ids=macro_commit.committed_child_ids,
    candidates_by_id=candidates_by_id,
    transport_kind=inp.transport_kind,
)
```

- [ ] **Step 4: Add regression test on greenfield fixture**

```python
def test_pipeline_result_includes_actual_committed_output(inp_from_fixture):
    result = run_rttp_pipeline(inp_from_fixture, ...)
    assert result.actual_committed_output_per_min is not None
    assert result.actual_committed_output_per_min.endswith("0000")  # 4dp
```

- [ ] **Step 5: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py -v --tb=short -k "actual_committed"
python -m ruff check django_apps/asteroid_lab/optimization/pipeline.py
```

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/optimization/pipeline.py tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py
git commit -m "feat(rttp): attach actual committed throughput to pipeline result"
```

---

### Task 4: Persist on `solver_summary` + runtime entry

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/rttp_solver_summary.py`
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_solver_summary.py`

- [ ] **Step 1: Failing summary test**

```python
def test_build_rttp_solver_summary_includes_actual_committed_when_provided() -> None:
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=2,
        normal_count=2,
        commit_order=("a", "b"),
        algorithm_steps=(),
        actual_committed_output_per_min="960.0000",
    )
    assert summary["actual_committed_output_per_min"] == "960.0000"
```

- [ ] **Step 2: Add kwarg to `build_rttp_solver_summary`**

```python
actual_committed_output_per_min: str | None = None,
...
if actual_committed_output_per_min is not None:
    summary["actual_committed_output_per_min"] = actual_committed_output_per_min
```

**Do not** change `throughput_budget_satisfied` in PR-2b (still `pipeline_ok`).

- [ ] **Step 3: Wire `solver_runtime_entry`**

```python
summary = build_rttp_solver_summary(
    ...
    actual_committed_output_per_min=pipeline_result.actual_committed_output_per_min,
)
```

- [ ] **Step 4: pytest + ruff**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_solver_summary.py -v --tb=short -k actual_committed
python -m ruff check django_apps/asteroid_lab/optimization/rttp_solver_summary.py django_apps/asteroid_lab/services/solver_runtime_entry.py
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/optimization/rttp_solver_summary.py django_apps/asteroid_lab/services/solver_runtime_entry.py tests/unit/asteroid_lab/test_rttp_solver_summary.py
git commit -m "feat(asteroid_lab): persist actual committed throughput on solver summary"
```

---

### Task 5: Lab DTO + card 5 subtitle

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`
- Modify: `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

- [ ] **Step 1: Test `actual_output_status` available when key present**

```python
row = lab_run_summary_from_solver_summary(
    run_id=1,
    status="completed",
    solver_summary={"actual_committed_output_per_min": "480.0000", "confirmed_count": 1},
)
assert row["rttp"]["actual_output_status"] == "available"
assert row["rttp"]["actual_committed_output_per_min"] == "480.0000"
```

- [ ] **Step 2: Update JS card 5 subtitle** (`updateLabStatCards` or equivalent)

When `rttp.actual_output_status === "available"`, subtitle = `shapezUiT("Committed output")` + `formatCompactNumber(actual)` + unit suffix from capacity primary unit.

Remove `actual output pending` string for available runs.

- [ ] **Step 3: pytest + manual smoke optional**

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v --tb=short
```

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/services/solver_run_lab_summary.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py django_apps/web/static/web/js/asteroid_miner_layout_lab.js
git commit -m "feat(web): show actual committed throughput on Lab card 5"
```

---

## Plan gate (pre-merge)

- [ ] `actual_committed_output_per_min` computed only from committed IDs + `MiningExtractionRule`
- [ ] No `throughput_target_percent` / target / budget changes
- [ ] `throughput_budget_satisfied` still aliases `pipeline_ok` until PR-2c
- [ ] Macro path uses `committed_child_ids`
- [ ] Narrow pytest green

```powershell
python -m pytest tests/unit/asteroid_lab/test_committed_throughput_summary.py tests/unit/asteroid_lab/test_rttp_solver_summary.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/services/committed_throughput_summary.py django_apps/asteroid_lab/optimization/pipeline.py
```
