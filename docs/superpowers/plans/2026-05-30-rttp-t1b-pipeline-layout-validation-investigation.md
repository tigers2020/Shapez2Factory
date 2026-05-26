# T1b Pipeline Layout Validation Investigation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Read-only E-track investigation — identify the first failing `validate_final_layout` assert (**FL-xx**) on diagnostic canon `copy-import-495e552c`, confirm catalog audit pass, classify T1b vs T2 causality, and publish an investigation report with owner matrix.

**Architecture:** Add investigation-only tooling under `harness/investigation/` that mirrors `validate_final_layout` assert order without modifying production validation. Capture pipeline inputs via `wraps` on `validate_pipeline_layout` during a canon-slug solver run. Parse persisted `algorithm_steps` for E.2/E.3 forensics. No runtime behavior changes.

**Tech Stack:** Python 3.12+, Django 5.2, pytest, ruff, existing RTTP pipeline (`run_solver_runtime_for_project`, `validate_pipeline_layout`).

**Design spec:** [`docs/superpowers/specs/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md`](../specs/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md)

---

## File structure

| File | Responsibility |
|------|----------------|
| `harness/investigation/__init__.py` | Package marker for investigation tooling |
| `harness/investigation/rttp_final_layout_assert_probe.py` | FL-xx diagnostic probe (mirrors assert order) |
| `harness/investigation/rttp_t1b_step_forensics.py` | Parse `algorithm_steps` for commit/catalog metrics |
| `tests/investigation/test_rttp_final_layout_assert_probe.py` | Unit tests for probe parity with known failures |
| `tests/investigation/test_rttp_t1b_canon_slug_layout_probe.py` | Integration: canon slug → FL-xx + forensics |
| `docs/superpowers/reports/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-report.md` | Final evidence table + owner matrix |
| `documents/ai/current_plan.md` | ACTIVE → CLOSED when report complete |

**Not modified in E phase:** `final_validation.py`, `catalog_layout_validation.py`, `pipeline.py`, throughput policy, slug data.

---

## Spec → plan coverage

| Spec section | Plan task |
|--------------|-----------|
| §5 FL-xx taxonomy | Task 1–2 |
| §6 E.2 catalog confirmation | Task 4, Task 6 |
| §7 E.3 pipeline composition | Task 4, Task 6 |
| §8 E.4 T2 causality | Task 6 |
| §9 Method 1 replay harness | Task 3–4 |
| §9 Method 2 step forensics | Task 4 |
| §10 Deliverables / §11 Acceptance | Task 6–7 |

---

### Task 1: Investigation package + FL-xx probe

**Files:**
- Create: `harness/investigation/__init__.py`
- Create: `harness/investigation/rttp_final_layout_assert_probe.py`
- Test: `tests/investigation/test_rttp_final_layout_assert_probe.py`

- [ ] **Step 1: Create package marker**

Create `harness/investigation/__init__.py`:

```python
"""Read-only RTTP investigation tooling (E-track; not solver input)."""
```

- [ ] **Step 2: Write failing unit test (FL-03 overlap)**

Create `tests/investigation/test_rttp_final_layout_assert_probe.py`:

```python
"""Unit tests for read-only final_layout assert probe (E-track)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from harness.investigation.rttp_final_layout_assert_probe import (
    FinalLayoutAssertCode,
    diagnose_final_layout,
)


def _minimal_pattern_e() -> BundlePattern:
    return BundlePattern(
        pattern_id="probe_test_e_len0",
        extension_count=0,
        occupied_offsets=frozenset({(0, 0)}),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_dir="E",
        fixed_output_transport_offset=(1, 0),
        output_stub_offset=(2, 0),
        throughput_factor=4,
        topology_kind="test",
    )


def _bundle_candidate(
    candidate_id: str,
    anchor: Coord,
    *,
    occupied: frozenset[Coord],
    output_stub: Coord,
    reachable: bool = True,
) -> BundleCandidate:
    pattern = _minimal_pattern_e()
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=output_stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=pattern.throughput_factor,
        route_probe_cost=1,
        reachable=reachable,
        catalog_placement_ref=None,
    )


def test_diagnose_fl03_occupied_overlap(
    greenfield_optimization_input,
) -> None:
    inp = greenfield_optimization_input
    a = _bundle_candidate("a", (0, 0), occupied=frozenset({(0, 0)}), output_stub=(2, 0))
    b = _bundle_candidate("b", (0, 0), occupied=frozenset({(0, 0)}), output_stub=(2, 0))
    code, detail = diagnose_final_layout(
        (a.candidate_id, b.candidate_id),
        frozenset(),
        {a.candidate_id: a, b.candidate_id: b},
        inp,
    )
    assert code is FinalLayoutAssertCode.FL_03
    assert detail["candidate_id"] == "b"
    assert detail["overlap_coords"]


def test_diagnose_fl07_reserved_vs_occupied(
    greenfield_optimization_input,
) -> None:
    inp = greenfield_optimization_input
    ext = _bundle_candidate("ext", (0, 0), occupied=frozenset({(0, 0)}), output_stub=(2, 0))
    code, detail = diagnose_final_layout(
        (ext.candidate_id,),
        frozenset({(0, 0), (1, 0)}),
        {ext.candidate_id: ext},
        inp,
    )
    assert code is FinalLayoutAssertCode.FL_07
    assert detail["reserved_vs_occupied"]


def test_diagnose_fl06_stub_not_in_reserved_when_reserved_nonempty(
    greenfield_optimization_input,
) -> None:
    inp = greenfield_optimization_input
    ext = _bundle_candidate("ext", (5, 5), occupied=frozenset({(5, 5)}), output_stub=(7, 5))
    code, detail = diagnose_final_layout(
        (ext.candidate_id,),
        frozenset({(5, 5)}),
        {ext.candidate_id: ext},
        inp,
    )
    assert code is FinalLayoutAssertCode.FL_06
    assert detail["output_stub"] == (7, 5)
    assert detail["reserved_route_cells_nonempty"] is True


def test_diagnose_fl09_unreachable(greenfield_optimization_input) -> None:
    inp = greenfield_optimization_input
    bad = _bundle_candidate(
        "bad",
        (0, 0),
        occupied=frozenset({(0, 0)}),
        output_stub=(2, 0),
        reachable=False,
    )
    code, detail = diagnose_final_layout(
        (bad.candidate_id,),
        frozenset(),
        {bad.candidate_id: bad},
        inp,
    )
    assert code is FinalLayoutAssertCode.FL_09
    assert detail["candidate_id"] == "bad"


def test_diagnose_ok_matches_validate_final_layout(
    greenfield_optimization_input,
) -> None:
    from django_apps.asteroid_lab.optimization.validation.final_validation import (
        validate_final_layout,
    )

    inp = greenfield_optimization_input
    ok = _bundle_candidate("ok", (0, 0), occupied=frozenset({(0, 0)}), output_stub=(2, 0))
    committed = (ok.candidate_id,)
    reserved = frozenset()
    by_id = {ok.candidate_id: ok}
    code, _ = diagnose_final_layout(committed, reserved, by_id, inp)
    assert code is FinalLayoutAssertCode.FL_OK
    assert validate_final_layout(committed, reserved, by_id, inp) is True
```

- [ ] **Step 3: Run test to verify it fails**

Run:

```bash
python -m pytest tests/investigation/test_rttp_final_layout_assert_probe.py -v
```

Expected: FAIL — `ModuleNotFoundError: harness.investigation.rttp_final_layout_assert_probe`

- [ ] **Step 4: Implement probe module**

Create `harness/investigation/rttp_final_layout_assert_probe.py`:

```python
"""Read-only final_layout assert probe for E-track T1b investigation.

Mirrors assert order in final_validation.validate_final_layout without mutating production code.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput


class FinalLayoutAssertCode(StrEnum):
    FL_OK = "FL-OK"
    FL_01 = "FL-01"
    FL_02 = "FL-02"
    FL_03 = "FL-03"
    FL_04 = "FL-04"
    FL_05 = "FL-05"
    FL_06 = "FL-06"
    FL_07 = "FL-07"
    FL_08 = "FL-08"
    FL_09 = "FL-09"


def diagnose_final_layout(
    committed_ids: tuple[str, ...],
    reserved_route_cells: frozenset[Coord],
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
) -> tuple[FinalLayoutAssertCode, dict[str, Any]]:
    if not committed_ids:
        return FinalLayoutAssertCode.FL_01, {"committed_count": 0}

    occupied_seen: set[tuple[int, int]] = set()
    fot_seen: set[tuple[int, int]] = set()
    for candidate_id in committed_ids:
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            return FinalLayoutAssertCode.FL_02, {"candidate_id": candidate_id}

        overlap = candidate.occupied_cells & frozenset(occupied_seen)
        if overlap:
            return FinalLayoutAssertCode.FL_03, {
                "candidate_id": candidate_id,
                "overlap_coords": sorted(overlap),
            }

        fot_cell = fixed_output_transport_cell(candidate)
        if fot_cell in inp.mineable_cells:
            return FinalLayoutAssertCode.FL_04, {
                "candidate_id": candidate_id,
                "fot_cell": fot_cell,
            }

        fot_on_prior_occupied = fot_cell in occupied_seen
        occupied_on_prior_fot = bool(candidate.occupied_cells & frozenset(fot_seen))
        if fot_on_prior_occupied or occupied_on_prior_fot:
            return FinalLayoutAssertCode.FL_05, {
                "candidate_id": candidate_id,
                "fot_cell": fot_cell,
                "fot_on_prior_occupied": fot_on_prior_occupied,
                "occupied_on_prior_fot": occupied_on_prior_fot,
            }

        occupied_seen.update(candidate.occupied_cells)
        fot_seen.add(fot_cell)

        if candidate.output_stub not in reserved_route_cells and reserved_route_cells:
            return FinalLayoutAssertCode.FL_06, {
                "candidate_id": candidate_id,
                "output_stub": candidate.output_stub,
                "reserved_route_cells_nonempty": True,
            }

    reserved_vs_occupied = reserved_route_cells & frozenset(occupied_seen)
    if reserved_vs_occupied:
        return FinalLayoutAssertCode.FL_07, {
            "reserved_vs_occupied": sorted(reserved_vs_occupied),
        }

    for candidate_id in committed_ids:
        candidate = candidates_by_id[candidate_id]
        if not candidate.occupied_cells.issubset(inp.mineable_cells):
            outside = sorted(candidate.occupied_cells - inp.mineable_cells)
            return FinalLayoutAssertCode.FL_08, {
                "candidate_id": candidate_id,
                "outside_mineable_coords": outside,
            }
        if not candidate.reachable:
            return FinalLayoutAssertCode.FL_09, {"candidate_id": candidate_id}

    return FinalLayoutAssertCode.FL_OK, {"committed_count": len(committed_ids)}


__all__ = ["FinalLayoutAssertCode", "diagnose_final_layout"]
```

- [ ] **Step 5: Run unit tests**

Run:

```bash
python -m pytest tests/investigation/test_rttp_final_layout_assert_probe.py -v
```

Expected: all PASS

- [ ] **Step 6: Ruff on new paths**

Run:

```bash
python -m ruff check harness/investigation tests/investigation/test_rttp_final_layout_assert_probe.py
```

Expected: no violations

---

### Task 2: Step forensics helper (E.2 / E.3)

**Files:**
- Create: `harness/investigation/rttp_t1b_step_forensics.py`
- Test: extend `tests/investigation/test_rttp_final_layout_assert_probe.py`

- [ ] **Step 1: Write failing test for forensics parser**

Append to `tests/investigation/test_rttp_final_layout_assert_probe.py`:

```python
from harness.investigation.rttp_t1b_step_forensics import extract_t1b_forensics


def test_extract_t1b_forensics_from_algorithm_steps() -> None:
    steps = [
        {
            "step_id": "rttp.commit",
            "passed": False,
            "metrics": {
                "validation_passed": False,
                "committed_ids": ["c1", "c2"],
                "conflict_count": 0,
            },
        },
        {
            "step_id": "rttp.catalog_placement_validation",
            "passed": True,
            "metrics": {
                "matched_count": 2,
                "mismatch_candidate_count": 0,
                "catalog_error_issue_codes": [],
            },
        },
    ]
    forensics = extract_t1b_forensics(steps)
    assert forensics["commit_passed"] is False
    assert forensics["validation_passed"] is False
    assert forensics["committed_count"] == 2
    assert forensics["catalog_passed"] is True
    assert forensics["catalog_mismatch_count"] == 0
    assert forensics["pipeline_composition_anomaly"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/investigation/test_rttp_final_layout_assert_probe.py::test_extract_t1b_forensics_from_algorithm_steps -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Implement forensics helper**

Create `harness/investigation/rttp_t1b_step_forensics.py`:

```python
"""Parse algorithm_steps for T1b investigation forensics (E.2 / E.3)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId


def _step_metrics(steps: Sequence[Mapping[str, object]], step_id: str) -> Mapping[str, object]:
    for step in steps:
        if str(step.get("step_id")) == step_id:
            metrics = step.get("metrics")
            if isinstance(metrics, Mapping):
                return metrics
    return {}


def extract_t1b_forensics(
    algorithm_steps: Sequence[Mapping[str, object]],
) -> dict[str, Any]:
    commit_metrics = _step_metrics(algorithm_steps, RttpAlgorithmStepId.RTTP_COMMIT.value)
    catalog_metrics = _step_metrics(
        algorithm_steps,
        RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value,
    )

    commit_step = next(
        (s for s in algorithm_steps if str(s.get("step_id")) == RttpAlgorithmStepId.RTTP_COMMIT.value),
        None,
    )
    catalog_step = next(
        (
            s
            for s in algorithm_steps
            if str(s.get("step_id")) == RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value
        ),
        None,
    )

    commit_passed = bool(commit_step.get("passed")) if commit_step else None
    validation_passed = commit_metrics.get("validation_passed")
    catalog_passed = bool(catalog_step.get("passed")) if catalog_step else None

    committed_ids = commit_metrics.get("committed_ids")
    committed_count = len(committed_ids) if isinstance(committed_ids, list) else 0

    mismatch_raw = catalog_metrics.get("mismatch_candidate_count")
    catalog_mismatch_count = int(mismatch_raw) if isinstance(mismatch_raw, int) else None

    pipeline_composition_anomaly = (
        commit_passed is not None
        and validation_passed is not None
        and commit_passed != validation_passed
    )

    return {
        "commit_passed": commit_passed,
        "validation_passed": validation_passed,
        "committed_count": committed_count,
        "conflict_count": commit_metrics.get("conflict_count"),
        "catalog_passed": catalog_passed,
        "catalog_mismatch_count": catalog_mismatch_count,
        "catalog_error_issue_codes": catalog_metrics.get("catalog_error_issue_codes"),
        "pipeline_composition_anomaly": pipeline_composition_anomaly,
    }


__all__ = ["extract_t1b_forensics"]
```

- [ ] **Step 4: Run forensics test**

Run:

```bash
python -m pytest tests/investigation/test_rttp_final_layout_assert_probe.py::test_extract_t1b_forensics_from_algorithm_steps -v
```

Expected: PASS

---

### Task 3: Canon slug integration probe (Method 1)

**Files:**
- Create: `tests/investigation/test_rttp_t1b_canon_slug_layout_probe.py`

- [ ] **Step 1: Write integration test with validate_pipeline_layout wraps**

Create `tests/investigation/test_rttp_t1b_canon_slug_layout_probe.py`:

```python
"""E-track: diagnostic canon slug layout assert probe (read-only)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.validation.catalog_layout_validation import (
    validate_pipeline_layout,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import run_solver_runtime_for_project
from django_apps.web.services.asteroid_game_data_snapshot import (
    build_asteroid_game_data_snapshot_with_provenance,
)
from harness.investigation.rttp_final_layout_assert_probe import (
    FinalLayoutAssertCode,
    diagnose_final_layout,
)
from harness.investigation.rttp_t1b_step_forensics import extract_t1b_forensics

CANON_SLUG = "copy-import-495e552c"


@pytest.fixture(scope="module")
def canon_project_id() -> int:
    project = m.AsteroidProject.objects.filter(slug=CANON_SLUG).first()
    if project is None:
        pytest.skip(f"Canon slug {CANON_SLUG!r} not in DB — import map first")
    return int(project.id)


@pytest.mark.django_db
@pytest.mark.integration
@pytest.mark.slow
def test_canon_slug_t1b_layout_assert_probe(canon_project_id: int) -> None:
    captured: dict[str, object] = {}

    def _capture_validate_pipeline_layout(**kwargs: object) -> tuple[bool, object | None]:
        captured.update(kwargs)
        return validate_pipeline_layout(**kwargs)  # type: ignore[arg-type]

    build = build_asteroid_game_data_snapshot_with_provenance()
    with patch(
        "django_apps.asteroid_lab.optimization.pipeline.validate_pipeline_layout",
        side_effect=_capture_validate_pipeline_layout,
    ):
        result = run_solver_runtime_for_project(
            canon_project_id,
            game_data_snapshot=build.snapshot,
            game_data_provenance=build.provenance,
            catalog_slice=build.catalog_slice,
            throughput_target_percent=10,
        )

    assert captured, "validate_pipeline_layout was not invoked"
    committed_ids = captured["committed_ids"]
    reserved_route_cells = captured["reserved_route_cells"]
    candidates_by_id = captured["candidates_by_id"]
    inp = captured["inp"]

    code, detail = diagnose_final_layout(
        committed_ids,  # type: ignore[arg-type]
        reserved_route_cells,  # type: ignore[arg-type]
        candidates_by_id,  # type: ignore[arg-type]
        inp,  # type: ignore[arg-type]
    )

    steps = result.solver_summary.get("algorithm_steps") or []
    forensics = extract_t1b_forensics(steps)

    assert forensics["committed_count"] > 0
    assert forensics["catalog_passed"] is True
    assert forensics["validation_passed"] is False
    assert forensics["pipeline_composition_anomaly"] is False
    assert code is not FinalLayoutAssertCode.FL_OK, detail
```

- [ ] **Step 2: Run integration probe**

Run:

```bash
python -m pytest tests/investigation/test_rttp_t1b_canon_slug_layout_probe.py -v
```

Expected: PASS with `code` one of FL-03..FL-09 (record which in report). If SKIP (no slug in DB), run:

```bash
python manage.py run_solver --slug copy-import-495e552c --json
```

and note `solver_run_id` for report; re-run pytest after DB has canon project.

- [ ] **Step 3: Optional ops JSON forensics (Method 2)**

Run:

```powershell
python manage.py run_solver --slug copy-import-495e552c --throughput-target-percent 10 --json > var/log/t1b_investigation_run.json
```

Inspect `algorithm_steps` for `rttp.commit` and `rttp.catalog_placement_validation` — confirm Run 103 parity (catalog pass, commit fail).

---

### Task 4: Investigation report + owner matrix

**Files:**
- Create: `docs/superpowers/reports/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-report.md`

- [ ] **Step 1: Create report from probe results**

Create `docs/superpowers/reports/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-report.md` with filled sections (replace `<FL-xx>` with actual probe output):

```markdown
# T1b Pipeline Layout Validation — Investigation Report

**Date:** 2026-05-30  
**Canon slug:** `copy-import-495e552c`  
**Design spec:** [`2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md`](../specs/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md)

## Evidence table

| Run / replay | committed_count | catalog_passed | validation_passed | Primary FL-xx | detail |
|--------------|-----------------|----------------|-------------------|---------------|--------|
| Integration probe | `<N>` | true | false | `<FL-xx>` | `<json detail>` |
| Ops JSON (optional) | `<N>` | true | false | `<FL-xx or same>` | `solver_run_id=<id>` |

## E.2 Catalog audit

- `catalog_passed=true`, `mismatch_candidate_count=0`, `catalog_error_issue_codes=[]` — **confirmed**.

## E.3 Pipeline composition

- `commit.passed == validation_passed` — **no anomaly** (or document if true).

## E.4 T2 causality

- Classification: `<T2_independent | T2_derived_from_layout | inconclusive>`
- Notes: `throughput_target_shortfall` + `selection_goal_cap` observed; layout gate failed independently.

## Owner matrix (next track)

| FL-xx | Likely owner | Recommended next track |
|-------|--------------|------------------------|
| `<FL-xx>` | `<owner>` | `<fix spec / D / A-B / no-op>` |

## Conclusion

Primary T1b failure on diagnostic canon is **`<FL-xx>`**, not catalog audit mismatch.
```

- [ ] **Step 2: Self-review against spec §11 acceptance**

Checklist all boxes in spec §11; mark any inconclusive item explicitly.

---

### Task 5: Governance close (current_plan)

**Files:**
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Update Next focus**

Replace ACTIVE line with:

```markdown
**CLOSED (2026-05-30):** **E — T1b pipeline layout validation investigation** (read-only) — primary FL-xx on `copy-import-495e552c`; catalog audit pass confirmed. Spec: [`docs/superpowers/specs/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md`](../../docs/superpowers/specs/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-design.md) · plan: [`docs/superpowers/plans/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation.md`](../../docs/superpowers/plans/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation.md) · report: [`docs/superpowers/reports/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-report.md`](../../docs/superpowers/reports/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation-report.md).

**Recommended ACTIVE:** follow owner matrix — typically **fix spec for `<FL-xx>` owner** or **D** (throughput) only if T2_independent and T1b resolved.
```

Only apply CLOSED row **after** Task 4 report has real FL-xx (not placeholders).

---

### Task 6: Full gate (investigation scope)

- [ ] **Step 1: Run narrow tests**

```bash
python -m pytest tests/investigation/ -v
```

Expected: all PASS (or documented SKIP if canon slug absent)

- [ ] **Step 2: Ruff**

```bash
python -m ruff check harness/investigation tests/investigation
```

Expected: no violations

- [ ] **Step 3: Confirm no production validation files changed**

```bash
git diff --name-only django_apps/asteroid_lab/optimization/validation/
```

Expected: empty diff

---

## Self-review (plan author)

| Check | Result |
|-------|--------|
| Spec §5 FL-06/FL-05/FL-03·07 wording | Reflected in probe code |
| §3 non-goals | No production validation edits in tasks |
| Placeholder scan | Report template uses `<>` only until Task 4 fill |
| Type consistency | `diagnose_final_layout` signatures match `validate_final_layout` inputs |

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-30-rttp-t1b-pipeline-layout-validation-investigation.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with checkpoints

**Which approach?**
