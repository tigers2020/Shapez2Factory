# B-CS3 Validation Gate Boundary Audit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Axis B milestone B-CS3 by proving validation remains a read-only assertion gate (normal + macro + PR-C validation/replay boundary) via pytest — **no solver production code changes**.

**Architecture:** Extend/consolidate AST import guards and immutability/call-sentinel tests under `tests/unit/asteroid_lab/`. PASS authority is pytest only (not ops smoke). If audit finds a production leak, stop with `BLOCKED:` and open a separate fix PR — do not weaken criteria.

**Tech Stack:** Python 3.14, pytest, `ast`, `unittest.mock`, existing narrow-corridor / catalog test fixtures

**Spec:** [`docs/superpowers/specs/2026-05-24-b-cs3-validation-gate-audit-design.md`](../specs/2026-05-24-b-cs3-validation-gate-audit-design.md)

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Read | Spec (above) | B-CS3-1 … B-CS3-10, PASS/FAIL summary |
| Read | `documents/adr/ADR-003-final-validation-assertion-gate.md` | Canon |
| Read | `documents/Algorithm/asteroid_lab_08_validation.md` | Phase 8 contract |
| Read | `django_apps/asteroid_lab/optimization/validation/final_validation.py` | Primary audit target |
| Read | `django_apps/asteroid_lab/optimization/validation/catalog_layout_validation.py` | AND composition |
| Read | `django_apps/asteroid_lab/optimization/pipeline.py` | `_run_v01_rttp_pipeline`, `_run_macro_rttp_pipeline` ordering |
| Read | `tests/unit/asteroid_lab/test_validation_readonly_guards.py` | Extend AST pattern |
| Read | `tests/unit/asteroid_lab/test_rttp_lns.py` | Keep until superseded |
| Create | `tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py` | Primary B-CS3 suite |
| Modify | `tests/unit/asteroid_lab/test_validation_readonly_guards.py` | Add `final_validation.py` to guarded modules |
| Modify | `documents/ai/current_plan.md` | B-CS3 CLOSED on pass |
| Modify | `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | B-CS3 ✅ |

**Forbidden:** edits under `django_apps/asteroid_lab/optimization/**` (except if BLOCKED leak fix approved separately).

---

## Shared test constants (all tasks)

Add at top of `test_b_cs3_validation_gate_boundary.py`:

```python
"""B-CS3 — validation gate boundary audit (Axis B). Spec: 2026-05-24-b-cs3-validation-gate-audit-design."""

from __future__ import annotations

import ast
import copy
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]

_VALIDATION_MODULE_PATHS = (
    _REPO_ROOT / "django_apps/asteroid_lab/optimization/validation/final_validation.py",
    _REPO_ROOT / "django_apps/asteroid_lab/optimization/validation/catalog_layout_validation.py",
    _REPO_ROOT / "django_apps/asteroid_lab/adapters/catalog_placement_validation.py",
    _REPO_ROOT / "django_apps/asteroid_lab/adapters/catalog_placement_audit.py",
)

_FORBIDDEN_IMPORT_PREFIXES = (
    "django_apps.asteroid_lab.optimization.routing.route_probe",
    "django_apps.asteroid_lab.optimization.commit.local_lns",
    "django_apps.asteroid_lab.optimization.commit.incremental_commit",
    "django_apps.asteroid_lab.optimization.commit",
    "django_apps.asteroid_lab.optimization.candidates.candidate_generator",
    "django_apps.asteroid_lab.optimization.routing.route_domain",
    "django_apps.asteroid_lab.services.replay_pipeline_service",
    "django_apps.asteroid_lab.services.lab_rttp_snapshot_compose",
    "django_apps.asteroid_lab.replay",
    "django_apps.asteroid_lab.optimization.replay_sink",
)


class ValidationBoundaryViolation(AssertionError):
    """Raised by monkeypatch sentinels when validation calls forbidden APIs."""
```

Reuse `_forbidden_imports(path) -> list[str]` from `test_validation_readonly_guards.py` (copy or import privately — prefer copy to avoid cross-test coupling).

---

### Task 0 — Inventory (BLOCK gate)

**Files:** none (read-only)

- [ ] **Step 1: List validation entrypoints**

```powershell
python -c "from django_apps.asteroid_lab.optimization.validation import validate_final_layout; from django_apps.asteroid_lab.optimization.validation.catalog_layout_validation import validate_pipeline_layout; print('ok', validate_final_layout, validate_pipeline_layout)"
```

Expected: prints `ok` without import error.

- [ ] **Step 2: Confirm B-CS1 + D+ guards green**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_survivability.py tests/unit/asteroid_lab/test_validation_readonly_guards.py tests/unit/asteroid_lab/test_rttp_lns.py -v
```

Expected: all PASS.

- [ ] **Step 3: Record pipeline function names**

Open `django_apps/asteroid_lab/optimization/pipeline.py` and confirm:

- Normal v0.1 body: `_run_v01_rttp_pipeline` (lines ~241–376)
- Macro body: `_run_macro_rttp_pipeline` (lines ~379–548)
- Public entry: `run_rttp_pipeline` dispatches by config

If names differ on `master`, update this plan’s Task 4 AST targets to match — do **not** rename production functions in B-CS3.

---

### Task 1 — AST import boundary tests (B-CS3-1, B-CS3-8 partial, B-CS3-9 partial)

**Files:**

- Create: `tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py`
- Modify: `tests/unit/asteroid_lab/test_validation_readonly_guards.py`

**Maps to spec:** B-CS3-1, B-CS3-9 (import half)

- [ ] **Step 1: Write failing test — all validation modules AST-clean**

```python
def test_b_cs3_validation_modules_forbidden_imports_ast() -> None:
    violations: list[str] = []
    for module_path in _VALIDATION_MODULE_PATHS:
        violations.extend(_forbidden_imports(module_path))
    assert violations == [], "\n".join(violations)
```

- [ ] **Step 2: Run test**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py::test_b_cs3_validation_modules_forbidden_imports_ast -v
```

Expected: PASS if production already clean; if FAIL, **BLOCKED** — do not delete forbidden imports from production in B-CS3 without separate bug PR.

- [ ] **Step 3: Extend `test_validation_readonly_guards` guarded set**

In `test_validation_readonly_guards.py`, add `final_validation.py` to `_GUARDED_MODULES`:

```python
_FINAL_VALIDATION_MODULE = _REPO_ROOT / "django_apps/asteroid_lab/optimization/validation/final_validation.py"
_GUARDED_MODULES = (
    _VALIDATION_MODULE,
    _AUDIT_MODULE,
    _LAYOUT_VALIDATION_MODULE,
    _FINAL_VALIDATION_MODULE,
)
```

- [ ] **Step 4: Re-run both modules**

```powershell
python -m pytest tests/unit/asteroid_lab/test_validation_readonly_guards.py tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py::test_b_cs3_validation_modules_forbidden_imports_ast -v
```

Expected: PASS.

- [ ] **Step 5: Commit (tests only)**

```bash
git add tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py tests/unit/asteroid_lab/test_validation_readonly_guards.py
git commit -m "test(asteroid_lab): B-CS3 AST forbidden import boundaries for validation modules"
```

---

### Task 2 — Read-only immutability sentinel tests (B-CS3-2 … B-CS3-5)

**Files:**

- Modify: `tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py`
- Reuse: `tests/unit/asteroid_lab/test_validation_readonly_guards.py` (`_catalog_slice`, `_candidate` helpers)

**Maps to spec:** B-CS3-2 (five input classes), B-CS3-5 (placement via candidate cells)

- [ ] **Step 1: Write test — `validate_catalog_placements` candidate immutability**

Copy pattern from `test_validate_catalog_placements_does_not_mutate_candidate` in `test_validation_readonly_guards.py`; rename to `test_b_cs3_catalog_validation_does_not_mutate_candidate`.

- [ ] **Step 2: Write test — `validate_final_layout` candidate + commit inputs**

```python
from django_apps.asteroid_lab.optimization.validation.final_validation import validate_final_layout
from tests.unit.asteroid_lab.test_validation_readonly_guards import _catalog_slice, _candidate


def test_b_cs3_validate_final_layout_preserves_candidate_and_commit_inputs() -> None:
    sl = _catalog_slice()
  # build minimal OptimizationInput with mineable cells covering candidate footprint
    from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput, TransportKind

    ref = None  # or CatalogPlacementRef from test_validation_readonly_guards
    occupied = frozenset({(5, 7), (6, 7)})
    cand = _candidate(occupied=occupied, ref=ref)
    candidates_by_id = {"c1": cand}
    committed_ids = ("c1",)
    reserved = frozenset({(9, 7)})

    inp = OptimizationInput(
        mineable_cells=frozenset({(5, 7), (6, 7), (9, 7)}),
        transport_kind=TransportKind.SHAPE_BELT,
        catalog_slice=sl,
        topology_graph=(),  # use minimal valid empty topology per input_contracts
    )
    cand_before = copy.deepcopy(cand)
    reserved_before = copy.deepcopy(reserved)
    inp_before = copy.deepcopy(inp)

    result = validate_final_layout(committed_ids, reserved, candidates_by_id, inp)

    assert isinstance(result, bool)
    assert cand.occupied_cells == cand_before.occupied_cells
    assert cand.reachable == cand_before.reachable
    assert reserved == reserved_before
    assert inp.mineable_cells == inp_before.mineable_cells
```

**Note:** Adjust `OptimizationInput` constructor fields to match current `input_contracts.py` (read file first — plan shows intent; engineer must use exact required fields).

- [ ] **Step 3: Write test — `validate_pipeline_layout` calls `validate_final_layout` (B-CS3-10 prep)**

```python
def test_b_cs3_observe_only_still_runs_final_layout(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def _spy(*args, **kwargs):
        calls.append("final")
        return True

    monkeypatch.setattr(
        "django_apps.asteroid_lab.optimization.validation.catalog_layout_validation.validate_final_layout",
        _spy,
    )
    from django_apps.asteroid_lab.optimization.validation.catalog_layout_validation import (
        validate_pipeline_layout,
    )

    # minimal args — same inp/candidate setup as Step 2
    validate_pipeline_layout(
        committed_ids=("c1",),
        reserved_route_cells=frozenset({(9, 7)}),
        candidates_by_id={"c1": cand},
        inp=inp,
        catalog_mode="observe_only",
    )
    assert calls == ["final"]
```

- [ ] **Step 4: Run Task 2 tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py -k "b_cs3_validate or b_cs3_catalog" -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py
git commit -m "test(asteroid_lab): B-CS3 validation immutability sentinels"
```

---

### Task 3 — Reachable semantics + call sentinels (B-CS3-3, B-CS3-6)

**Files:**

- Modify: `tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py`

**Maps to spec:** B-CS3-3 (no route invention), B-CS3-6 (reachable assert-only)

- [ ] **Step 1: Write test — route probe not called during validation**

```python
def test_b_cs3_validate_final_layout_does_not_call_route_probe() -> None:
    from django_apps.asteroid_lab.optimization.validation import final_validation

    def _boom(*args, **kwargs):
        raise ValidationBoundaryViolation("route_probe called from validation")

    with patch(
        "django_apps.asteroid_lab.optimization.routing.route_probe.run_route_probe",
        side_effect=_boom,
    ):
        # also patch probe_route if incremental_commit re-export path exists
        with patch(
            "django_apps.asteroid_lab.optimization.commit.incremental_commit.probe_route",
            side_effect=_boom,
        ):
            validate_final_layout(committed_ids, reserved, candidates_by_id, inp)
```

Use the same minimal `inp` / `cand` fixture as Task 2. Expected: returns bool without raising `ValidationBoundaryViolation`.

- [ ] **Step 2: Write test — toggling reachable only affects assert outcome, not re-probe**

```python
def test_b_cs3_reachable_is_snapshot_assert_not_reprobe() -> None:
    cand_ok = replace(cand, reachable=True)
    cand_bad = replace(cand, reachable=False)
    assert validate_final_layout(("c1",), reserved, {"c1": cand_ok}, inp) is True
    assert validate_final_layout(("c1",), reserved, {"c1": cand_bad}, inp) is False
```

Import `replace` from `dataclasses`. Documents B-CS3-6: validation **reads** stored `reachable`; does not refresh it.

- [ ] **Step 3: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py -k "route_probe or reachable" -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py
git commit -m "test(asteroid_lab): B-CS3 reachable assert-only and no route_probe calls"
```

---

### Task 4 — Pipeline ordering tests (B-CS3-7, B-CS3-8)

**Files:**

- Modify: `tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py`

**Maps to spec:** B-CS3-7 (normal), B-CS3-8 (macro — no LNS required)

- [ ] **Step 1: Write AST ordering test for normal path**

```python
_PIPELINE_PATH = _REPO_ROOT / "django_apps/asteroid_lab/optimization/pipeline.py"


def _function_body_line_range(path: Path, func_name: str) -> tuple[int, int]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            assert node.end_lineno is not None
            return node.lineno, node.end_lineno
    raise AssertionError(f"{func_name} not found in {path.name}")


def _first_call_line(func_name: str, callee: str) -> int:
    start, end = _function_body_line_range(_PIPELINE_PATH, func_name)
    lines = _PIPELINE_PATH.read_text(encoding="utf-8-sig").splitlines()
    for lineno in range(start, end + 1):
        if callee in lines[lineno - 1]:
            return lineno
    raise AssertionError(f"{callee} not found in {func_name}")


def test_b_cs3_normal_pipeline_validation_after_lns_and_commit() -> None:
    commit_line = _first_call_line("_run_v01_rttp_pipeline", "incremental_commit(")
    lns_line = _first_call_line("_run_v01_rttp_pipeline", "run_local_lns(")
    validate_line = _first_call_line("_run_v01_rttp_pipeline", "validate_pipeline_layout(")
    assert commit_line < lns_line < validate_line
```

If `run_local_lns` is only referenced inside `if commit_result.conflicts:` block, assert `commit_line < validate_line` and `lns_line < validate_line` (LNS may be conditional — still must precede validation).

- [ ] **Step 2: Write macro ordering test**

```python
def test_b_cs3_macro_pipeline_validation_after_commit() -> None:
    commit_line = _first_call_line("_run_macro_rttp_pipeline", "incremental_commit_macro(")
    macro_validate_line = _first_call_line("_run_macro_rttp_pipeline", "validate_macro_layout(")
    assert commit_line < macro_validate_line
    body = _PIPELINE_PATH.read_text(encoding="utf-8-sig")
    func_start, func_end = _function_body_line_range(_PIPELINE_PATH, "_run_macro_rttp_pipeline")
    macro_body = "\n".join(body.splitlines()[func_start - 1 : func_end])
    assert "run_local_lns" not in macro_body, "macro path has no LNS today (observed fact)"
```

- [ ] **Step 3: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py -k pipeline -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py
git commit -m "test(asteroid_lab): B-CS3 pipeline validation ordering guards"
```

---

### Task 5 — PR-C validation/replay boundary absorption (B-CS3-9)

**Files:**

- Modify: `tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py`

**Maps to spec:** B-CS3-9 (partial PR-C only — not PR-B/D/E)

- [ ] **Step 1: Add replay/ORM forbidden prefixes to `_FORBIDDEN_IMPORT_PREFIXES`**

Ensure tuple includes:

```python
"django_apps.asteroid_lab.services.replay_pipeline_service",
"django_apps.asteroid_lab.services.replay_recorder",
"django_apps.asteroid_lab.services.lab_rttp_snapshot_compose",
"django_apps.asteroid_lab.models",
```

- [ ] **Step 2: Re-run AST test from Task 1**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py::test_b_cs3_validation_modules_forbidden_imports_ast -v
```

Expected: PASS. If FAIL on `catalog_placement_audit` importing something allowed for metrics-only observe path, document exception in test comment **only** if architect-approved — default is BLOCKED.

- [ ] **Step 3: Optional consolidation test — no `SolverRun` in validation modules**

```python
def test_b_cs3_validation_modules_do_not_reference_solver_run_orm() -> None:
    for path in _VALIDATION_MODULE_PATHS:
        text = path.read_text(encoding="utf-8-sig")
        assert "SolverRun" not in text
        assert "config_json" not in text
```

This is **supplementary** (source token); AST import test remains PASS authority.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py
git commit -m "test(asteroid_lab): B-CS3 PR-C validation replay import boundary"
```

---

### Task 6 — Regression gate (B-CS3 closure evidence)

**Files:** none

- [ ] **Step 1: Full B-CS3 module**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py -v
```

Expected: all PASS.

- [ ] **Step 2: Do not remove legacy guards**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_lns.py tests/unit/asteroid_lab/test_validation_readonly_guards.py -v
```

Expected: PASS.

- [ ] **Step 3: B-CS1 + narrow RTTP**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_commit_survivability.py -v
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v
```

Expected: PASS.

- [ ] **Step 4: Lint**

```powershell
python -m ruff check tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py tests/unit/asteroid_lab/test_validation_readonly_guards.py
```

Expected: clean.

- [ ] **Step 5: If any production leak found**

Stop. Emit `BLOCKED:` per spec. Do **not** mark B-CS3 CLOSED.

---

### Task 7 — Docs close

**Files:**

- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`

- [ ] **Step 1: Add CLOSED entry to `current_plan.md`**

Template:

```markdown
- B-CS3 — Validation gate boundary audit
  - Status: **CLOSED**
  - Spec: [`docs/superpowers/specs/2026-05-24-b-cs3-validation-gate-audit-design.md`](../../docs/superpowers/specs/2026-05-24-b-cs3-validation-gate-audit-design.md)
  - Plan: [`docs/superpowers/plans/2026-05-24-b-cs3-validation-gate-audit.md`](../../docs/superpowers/plans/2026-05-24-b-cs3-validation-gate-audit.md)
  - Evidence: `python -m pytest tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py` PASS; B-CS1 + narrow RTTP PASS
  - PR-C: validation/replay contamination portion absorbed; broader PR-C (PR-B/D/E) not closed here
```

Update **Next focus** to B-CS4 or reconstruction maintenance per roadmap.

- [ ] **Step 2: Roadmap B-CS3 row → ✅**

In `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`:

- B-CS3 table: ⬜ → ✅ with date
- Axis B progress note: B-CS3 closed
- Open next: B-CS4 replay narrow gate (ongoing)

- [ ] **Step 3: Commit docs**

```bash
git add documents/ai/current_plan.md docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md docs/superpowers/specs/2026-05-24-b-cs3-validation-gate-audit-design.md docs/superpowers/plans/2026-05-24-b-cs3-validation-gate-audit.md
git commit -m "docs: close B-CS3 validation gate boundary audit"
```

---

## Plan self-review (vs spec)

| Spec ID | Task |
|---------|------|
| B-CS3-1 | Task 1 AST |
| B-CS3-2 | Task 2 deepcopy sentinels |
| B-CS3-3 | Task 3 route_probe monkeypatch |
| B-CS3-4 | Task 2 topology via `inp` deepcopy |
| B-CS3-5 | Task 2 candidate cells |
| B-CS3-6 | Task 3 reachable tests |
| B-CS3-7 | Task 4 normal ordering |
| B-CS3-8 | Task 4 macro ordering |
| B-CS3-9 | Task 5 PR-C partial |
| B-CS3-10 | Task 2 observe_only spy |
| PASS/FAIL summary | Task 6 |
| No solver logic | File map forbidden |
| PR-C partial only | Task 5 + Task 7 wording |
| AST not source-word PASS | Task 1 + Task 5 note on supplementary token test |

No TBD placeholders in task steps.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-24-b-cs3-validation-gate-audit.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — run tasks in this session with executing-plans checkpoints  

Which approach do you want?
