# RTTP Throughput Policy — T2 Diagnostic Canon (D-PR) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist truthful T2 policy observability on RTTP runs so diagnostic canon `copy-import-495e552c` reports `expected_diagnostic_shortfall` without changing `throughput_budget_satisfied`, `issue_codes`, or `validation_passed` semantics.

**Architecture:** Pure classification in `contracts/rttp_ops_policy.py`; merge policy fields in `build_rttp_solver_summary` when `throughput_budget_fields` and `project_slug` are present; project slug loaded once in `solver_runtime_entry`; Lab summary projection + JS copy for non-milestone UX.

**Tech Stack:** Python 3.12+, Django 5.2, pytest, ruff, mypy (`django_apps config src`), vanilla Lab JS.

**Design spec (APPROVED):** [`docs/superpowers/specs/2026-05-30-rttp-throughput-policy-t2-diagnostic-canon-design.md`](../specs/2026-05-30-rttp-throughput-policy-t2-diagnostic-canon-design.md)

**D-GOV:** CLOSED 2026-05-30 — `current_plan.md` + roadmap updated; no runtime code in governance slice.

---

## File structure

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/contracts/rttp_ops_policy.py` | Slug registry + `classify_t2_policy` + stable token constants |
| `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | Merge policy dict after throughput fields |
| `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Load `AsteroidProject.slug`; pass to summary builder |
| `django_apps/asteroid_lab/services/solver_run_lab_summary.py` | Project policy fields into Lab `throughput_target` + top-level |
| `django_apps/asteroid_lab/management/commands/run_solver.py` | Optional stdout line for diagnostic shortfall |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | `runCapacityFailed` + issue label copy |
| `tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py` | Contract + summary + lab projection tests |
| `tests/unit/asteroid_lab/test_rttp_solver_summary.py` | Extend existing summary tests |
| `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` | Lab row projection |
| `tests/unit/web/test_run_solver_cli_t2_policy.py` | CLI stdout line (optional thin test) |

**Not modified:** `throughput_target.py` (A/C/D formulas), `pipeline.py` validation, `final_validation.py`, macro/GA.

---

## Spec → plan coverage

| Spec § | Task |
|--------|------|
| §4–§5 tokens | Task 1 |
| §6 `solver_summary` | Task 2 |
| §6 runtime slug | Task 3 |
| §6 Lab summary | Task 4 |
| §6 Lab JS | Task 5 |
| §6 CLI | Task 6 |
| §7 regression | Task 7 |
| §9 acceptance | Tasks 1–7 |
| §10 verification | Task 7 |

---

### Task 1: T2 policy contracts + unit tests

**Files:**
- Create: `django_apps/asteroid_lab/contracts/rttp_ops_policy.py`
- Create: `tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py`

- [ ] **Step 1: Write failing contract tests**

Create `tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py`:

```python
"""Track D — T2 throughput policy on diagnostic canon (observability only)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
    RTTP_DIAGNOSTIC_CANON_SLUG,
    T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP,
    T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
    T2_POLICY_STATUS_SATISFIED,
    T2_POLICY_STATUS_SHORTFALL,
    T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON,
    RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON,
    RTTP_OPS_SLUG_CLASS_UNKNOWN,
    classify_t2_policy,
)


def test_diagnostic_canon_shortfall_is_expected() -> None:
    row = classify_t2_policy(
        project_slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        throughput_budget_satisfied=False,
    )
    assert row.t2_policy_status == T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL
    assert row.t2_policy_reason == T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP
    assert row.diagnostic_expected_shortfall is True
    assert row.t3_ops_eligible is False
    assert row.t3_blocked_reason == T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON
    assert row.rttp_ops_slug_class == RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON


def test_unknown_slug_shortfall_not_expected() -> None:
    row = classify_t2_policy(
        project_slug="some-other-slug",
        throughput_budget_satisfied=False,
    )
    assert row.t2_policy_status == T2_POLICY_STATUS_SHORTFALL
    assert row.t2_policy_reason is None
    assert row.diagnostic_expected_shortfall is False
    assert row.t3_ops_eligible is False
    assert row.t3_blocked_reason is None
    assert row.rttp_ops_slug_class == RTTP_OPS_SLUG_CLASS_UNKNOWN


def test_satisfied_on_any_slug() -> None:
    row = classify_t2_policy(
        project_slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        throughput_budget_satisfied=True,
    )
    assert row.t2_policy_status == T2_POLICY_STATUS_SATISFIED
    assert row.t2_policy_reason is None
    assert row.diagnostic_expected_shortfall is False
    assert row.t3_ops_eligible is True
    assert row.t3_blocked_reason is None


def test_no_policy_when_budget_none() -> None:
    row = classify_t2_policy(
        project_slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        throughput_budget_satisfied=None,
    )
    assert row.t2_policy_status is None
    assert row.as_summary_fields() == {}


def test_as_summary_fields_keys() -> None:
    row = classify_t2_policy(
        project_slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        throughput_budget_satisfied=False,
    )
    fields = row.as_summary_fields()
    assert fields["t2_policy_status"] == T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL
    assert fields["diagnostic_expected_shortfall"] is True
    assert "throughput_budget_satisfied" not in fields
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py -v
```

Expected: FAIL — `ModuleNotFoundError: django_apps.asteroid_lab.contracts.rttp_ops_policy`

- [ ] **Step 3: Implement contracts module**

Create `django_apps/asteroid_lab/contracts/rttp_ops_policy.py`:

```python
"""RTTP ops authority tokens (T2 policy); not solver algorithm input."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RTTP_DIAGNOSTIC_CANON_SLUG = "copy-import-495e552c"

T2_POLICY_STATUS_SATISFIED = "satisfied"
T2_POLICY_STATUS_SHORTFALL = "shortfall"
T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL = "expected_diagnostic_shortfall"

T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP = "diagnostic_canon_route_feasible_gap"

T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON = (
    "t2_not_pass_capable_on_diagnostic_canon"
)

RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON = "diagnostic_canon"
RTTP_OPS_SLUG_CLASS_UNKNOWN = "unknown"

ALL_T2_POLICY_STATUSES: frozenset[str] = frozenset(
    {
        T2_POLICY_STATUS_SATISFIED,
        T2_POLICY_STATUS_SHORTFALL,
        T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
    }
)


def is_diagnostic_canon_slug(project_slug: str | None) -> bool:
    if not project_slug:
        return False
    return project_slug.strip() == RTTP_DIAGNOSTIC_CANON_SLUG


@dataclass(frozen=True, slots=True)
class T2PolicyClassification:
    t2_policy_status: str | None
    t2_policy_reason: str | None
    diagnostic_expected_shortfall: bool
    t3_ops_eligible: bool
    t3_blocked_reason: str | None
    rttp_ops_slug_class: str

    def as_summary_fields(self) -> dict[str, Any]:
        if self.t2_policy_status is None:
            return {}
        out: dict[str, Any] = {
            "t2_policy_status": self.t2_policy_status,
            "diagnostic_expected_shortfall": self.diagnostic_expected_shortfall,
            "t3_ops_eligible": self.t3_ops_eligible,
            "rttp_ops_slug_class": self.rttp_ops_slug_class,
        }
        if self.t2_policy_reason is not None:
            out["t2_policy_reason"] = self.t2_policy_reason
        if self.t3_blocked_reason is not None:
            out["t3_blocked_reason"] = self.t3_blocked_reason
        return out


def classify_t2_policy(
    *,
    project_slug: str | None,
    throughput_budget_satisfied: bool | None,
) -> T2PolicyClassification:
    if throughput_budget_satisfied is None:
        return T2PolicyClassification(
            t2_policy_status=None,
            t2_policy_reason=None,
            diagnostic_expected_shortfall=False,
            t3_ops_eligible=False,
            t3_blocked_reason=None,
            rttp_ops_slug_class=RTTP_OPS_SLUG_CLASS_UNKNOWN,
        )

    slug_class = (
        RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON
        if is_diagnostic_canon_slug(project_slug)
        else RTTP_OPS_SLUG_CLASS_UNKNOWN
    )

    if throughput_budget_satisfied:
        return T2PolicyClassification(
            t2_policy_status=T2_POLICY_STATUS_SATISFIED,
            t2_policy_reason=None,
            diagnostic_expected_shortfall=False,
            t3_ops_eligible=True,
            t3_blocked_reason=None,
            rttp_ops_slug_class=slug_class,
        )

    if is_diagnostic_canon_slug(project_slug):
        return T2PolicyClassification(
            t2_policy_status=T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
            t2_policy_reason=T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP,
            diagnostic_expected_shortfall=True,
            t3_ops_eligible=False,
            t3_blocked_reason=T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON,
            rttp_ops_slug_class=RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON,
        )

    return T2PolicyClassification(
        t2_policy_status=T2_POLICY_STATUS_SHORTFALL,
        t2_policy_reason=None,
        diagnostic_expected_shortfall=False,
        t3_ops_eligible=False,
        t3_blocked_reason=None,
        rttp_ops_slug_class=slug_class,
    )


__all__ = [
    "ALL_T2_POLICY_STATUSES",
    "RTTP_DIAGNOSTIC_CANON_SLUG",
    "T2PolicyClassification",
    "T2_POLICY_REASON_DIAGNOSTIC_CANON_ROUTE_FEASIBLE_GAP",
    "T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL",
    "T2_POLICY_STATUS_SATISFIED",
    "T2_POLICY_STATUS_SHORTFALL",
    "T3_BLOCKED_REASON_T2_NOT_PASS_CAPABLE_ON_DIAGNOSTIC_CANON",
    "RTTP_OPS_SLUG_CLASS_DIAGNOSTIC_CANON",
    "RTTP_OPS_SLUG_CLASS_UNKNOWN",
    "classify_t2_policy",
    "is_diagnostic_canon_slug",
]
```

- [ ] **Step 4: Run contract tests**

Run:

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Ruff on new files**

Run:

```powershell
python -m ruff check django_apps/asteroid_lab/contracts/rttp_ops_policy.py tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py
```

Expected: no errors

---

### Task 2: Merge policy into `build_rttp_solver_summary`

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/rttp_solver_summary.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_solver_summary.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py`

- [ ] **Step 1: Write failing summary test**

Append to `tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py`:

```python
from django_apps.asteroid_lab.contracts.rttp_ops_policy import RTTP_DIAGNOSTIC_CANON_SLUG
from django_apps.asteroid_lab.optimization.rttp_solver_summary import build_rttp_solver_summary


def test_build_rttp_solver_summary_merges_t2_policy_for_diagnostic_canon() -> None:
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=32,
        normal_count=127,
        commit_order=("a",),
        algorithm_steps=(),
        project_slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        throughput_budget_fields={
            "throughput_budget_satisfied": False,
            "throughput_target_percent": 10,
            "target_throughput_per_min": "7536.0000",
            "actual_committed_output_per_min": "3840.0000",
            "throughput_shortfall_per_min": "3696.0000",
            "reconstruction_max_throughput_per_min": "75360.0000",
        },
    )
    assert summary["validation_passed"] is True
    assert summary["throughput_budget_satisfied"] is False
    assert "throughput_target_shortfall" in summary["issue_codes"]
    assert summary["t2_policy_status"] == "expected_diagnostic_shortfall"
    assert summary["diagnostic_expected_shortfall"] is True
    assert summary["t3_ops_eligible"] is False
```

- [ ] **Step 2: Run test — expect FAIL**

Run:

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py::test_build_rttp_solver_summary_merges_t2_policy_for_diagnostic_canon -v
```

Expected: FAIL — unexpected keyword `project_slug`

- [ ] **Step 3: Implement summary merge**

In `rttp_solver_summary.py`:

1. Import:

```python
from django_apps.asteroid_lab.contracts.rttp_ops_policy import classify_t2_policy
```

2. Add parameter to `build_rttp_solver_summary`:

```python
    project_slug: str | None = None,
```

3. After the `throughput_shortfall_reason` block (before `return summary`), add:

```python
    if throughput_budget_fields is not None:
        policy = classify_t2_policy(
            project_slug=project_slug,
            throughput_budget_satisfied=summary.get("throughput_budget_satisfied"),
        )
        summary.update(policy.as_summary_fields())
```

- [ ] **Step 4: Run tests**

Run:

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py tests/unit/asteroid_lab/test_rttp_solver_summary.py -v
```

Expected: all PASS

- [ ] **Step 5: Guard — policy does not flip validation**

Add to `test_rttp_solver_summary.py`:

```python
def test_t2_policy_does_not_change_validation_passed() -> None:
    from django_apps.asteroid_lab.contracts.rttp_ops_policy import RTTP_DIAGNOSTIC_CANON_SLUG

    summary = build_rttp_solver_summary(
        pipeline_ok=False,
        committed_count=0,
        normal_count=0,
        commit_order=(),
        algorithm_steps=(),
        project_slug=RTTP_DIAGNOSTIC_CANON_SLUG,
        throughput_budget_fields={"throughput_budget_satisfied": False},
    )
    assert summary["validation_passed"] is False
    assert summary["t2_policy_status"] == "expected_diagnostic_shortfall"
```

---

### Task 3: Wire `project_slug` in runtime entry

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`

- [ ] **Step 1: Load slug at start of `_run_rttp_solver_for_map_input`**

After `run_id = int(run_dto.id)` (or before `build_rttp_solver_summary` call), add:

```python
    project_slug: str | None = (
        m.AsteroidProject.objects.filter(pk=int(project_id))
        .values_list("slug", flat=True)
        .first()
    )
```

- [ ] **Step 2: Pass slug into summary builder**

In the `build_rttp_solver_summary(...)` call (~line 704), add:

```python
        project_slug=project_slug,
```

- [ ] **Step 3: Run narrow RTTP tests**

Run:

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py tests/unit/asteroid_lab/test_solver_runtime_entry_catalog_summary.py -v
```

Expected: PASS

---

### Task 4: Lab summary projection

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`
- Modify: `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`

- [ ] **Step 1: Write failing lab summary test**

Append to `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`:

```python
from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
    RTTP_DIAGNOSTIC_CANON_SLUG,
    T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
)


def test_lab_run_summary_projects_t2_policy_fields() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=200,
        status="completed",
        solver_summary={
            "validation_passed": True,
            "throughput_budget_satisfied": False,
            "actual_committed_output_per_min": "3840.0000",
            "target_throughput_per_min": "7536.0000",
            "throughput_target_percent": 10,
            "reconstruction_max_throughput_per_min": "75360.0000",
            "t2_policy_status": T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
            "diagnostic_expected_shortfall": True,
            "t3_ops_eligible": False,
            "issue_codes": ["throughput_target_shortfall"],
        },
    )
    assert row["diagnostic_expected_shortfall"] is True
    assert row["t3_ops_eligible"] is False
    assert row["throughput_target"]["t2_policy_status"] == T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL
```

- [ ] **Step 2: Run test — expect FAIL**

Run:

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py::test_lab_run_summary_projects_t2_policy_fields -v
```

- [ ] **Step 3: Implement projection**

In `_section_throughput_target`, extend `keys` tuple and return dict:

```python
        "t2_policy_status",
        "t2_policy_reason",
        "diagnostic_expected_shortfall",
        "t3_ops_eligible",
        "t3_blocked_reason",
        "rttp_ops_slug_class",
```

Map from `summary.get(...)` with `_PLACEHOLDER` when missing.

In `lab_run_summary_from_solver_summary`, add top-level passthrough:

```python
        "diagnostic_expected_shortfall": bool(
            solver_summary.get("diagnostic_expected_shortfall", False)
        ),
        "t3_ops_eligible": solver_summary.get("t3_ops_eligible"),
```

(use `None` or omit when not present — match existing `throughput_budget_satisfied` null pattern)

- [ ] **Step 4: Run lab summary tests**

Run:

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v
```

Expected: PASS

---

### Task 5: Lab UI copy

**Files:**
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

- [ ] **Step 1: Update `runCapacityFailed`**

At top of function, after null check:

```javascript
    if (run.diagnostic_expected_shortfall === true) {
      return false;
    }
```

- [ ] **Step 2: Add status helper (near `capacityFailedStatusText`)**

```javascript
  function diagnosticT2ShortfallStatusText(run) {
    if (!run || run.diagnostic_expected_shortfall !== true) return null;
  const msgid =
      "Expected diagnostic T2 shortfall (route-feasible vs reconstruction max); not a regression gate.";
    return typeof shapezUiT === "function" ? shapezUiT(msgid) : msgid;
  }
```

In `capacityFailedStatusText`, if `diagnosticT2ShortfallStatusText(run)` non-null, return that string early.

- [ ] **Step 3: Issue label suffix in `formatLabIssueCodeLabel`**

When `key === "throughput_target_shortfall"` and `run.diagnostic_expected_shortfall === true`, append:

```javascript
        const suffix =
          typeof shapezUiT === "function"
            ? shapezUiT(" (expected on diagnostic canon)")
            : " (expected on diagnostic canon)";
        return baseLabel + suffix;
```

(apply to both numeric shortfall branch and msgid branch)

- [ ] **Step 4: Manual smoke (optional)**

Load Lab for `copy-import-495e552c` after a run with policy fields; confirm run row does not show generic capacity-failed when `diagnostic_expected_shortfall` is true.

---

### Task 6: CLI observability line

**Files:**
- Modify: `django_apps/asteroid_lab/management/commands/run_solver.py`

- [ ] **Step 1: Write failing CLI test**

Create `tests/unit/asteroid_lab/test_run_solver_cli_t2_policy_line.py`:

```python
"""CLI prints t2_policy line when diagnostic expected shortfall is set."""

from __future__ import annotations

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
    T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import SolverRuntimeEntryResult


@pytest.mark.django_db
def test_run_solver_prints_t2_policy_line_for_diagnostic_shortfall() -> None:
    summary = {
        "validation_passed": True,
        "diagnostic_expected_shortfall": True,
        "t2_policy_status": T2_POLICY_STATUS_EXPECTED_DIAGNOSTIC_SHORTFALL,
        "issue_codes": ["throughput_target_shortfall"],
    }
    result = SolverRuntimeEntryResult(
        ok=True,
        solver_run_id=999,
        lab_replay_frames_json=[],
        replay_track_metrics={},
        solver_summary=summary,
        validation_passed=True,
    )
    out = StringIO()
    with patch(
        "django_apps.asteroid_lab.management.commands.run_solver.run_solver_runtime_for_project",
        return_value=result,
    ):
        with patch(
            "django_apps.asteroid_lab.management.commands.run_solver.build_asteroid_game_data_snapshot_with_provenance",
        ):
            call_command("run_solver", slug="copy-import-495e552c", stdout=out)
    text = out.getvalue()
    assert "t2_policy: expected_diagnostic_shortfall" in text
```

Adjust mocks to match existing `test_run_solver` / web config test patterns if import paths differ.

- [ ] **Step 2: Implement stdout line in `_print_human_summary`**

After `issue_codes` block:

```python
        if summary.get("diagnostic_expected_shortfall"):
            lines.append(
                "t2_policy: expected_diagnostic_shortfall "
                "(diagnostic canon; T3 ops not applicable)"
            )
```

- [ ] **Step 3: Run CLI test**

```powershell
python -m pytest tests/unit/asteroid_lab/test_run_solver_cli_t2_policy_line.py -v
```

---

### Task 7: Verification + D-PR close metadata

**Files:**
- Modify: `documents/ai/current_plan.md` (after merge)
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` (D-PR CLOSED row)

- [ ] **Step 1: Narrow pytest**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py tests/unit/asteroid_lab/test_rttp_solver_summary.py tests/unit/asteroid_lab/test_solver_run_lab_summary.py -v
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v
```

- [ ] **Step 2: Standing gates**

```powershell
powershell -File scripts/test_optimization_contamination.ps1
python -m ruff check django_apps/asteroid_lab/contracts/rttp_ops_policy.py django_apps/asteroid_lab/optimization/rttp_solver_summary.py django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/asteroid_lab/services/solver_run_lab_summary.py
```

- [ ] **Step 3: Optional canon ops readback**

```powershell
python manage.py run_solver --slug copy-import-495e552c --no-replay --throughput-target-percent 10
```

Confirm readback per spec §10.

- [ ] **Step 4: Update `current_plan.md`**

- ACTIVE: Track **B** pass-capable slug (or next queue item)
- CLOSED: D-PR with date + `solver_run_id` evidence if ops run executed

---

## Self-review (plan author)

| Check | Result |
|-------|--------|
| Spec §4–§7 covered | Tasks 1–7 |
| No placeholders | All steps have concrete paths/code |
| `project_slug` naming consistent | Tasks 2–3 |
| Forbidden: fake `throughput_budget_satisfied` | Tests assert false preserved |
| Free-form strings | All tokens in `rttp_ops_policy.py` |

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-30-rttp-throughput-policy-t2-diagnostic-canon.md`.

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  

**2. Inline Execution** — execute in this session with executing-plans checkpoints  

Which approach do you want?
