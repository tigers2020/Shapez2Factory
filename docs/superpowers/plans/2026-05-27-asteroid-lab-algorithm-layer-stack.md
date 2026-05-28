# Asteroid Lab — Algorithm Layer Stack — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Plan review (2026-05-27):** **APPROVE AFTER PLAN PATCH** — patches below applied (budget clock injection, token scan policy, optimization scope, PR-3 split, extra gates).

**Goal:** Introduce `layers/` stack (L1 facade `layer_01_reconstruction` + L2–L5), `stack_runner` with exclusive 60s budget, typed contracts per [layer stack design](../specs/2026-05-27-asteroid-lab-algorithm-layer-stack-design.md), and gates — then wire `run_solver` when MVP passes.

**Architecture:** Keep `reconstruction/` implementation; add `layers/layer_01_reconstruction` facade; greenfield L2–L5 with **no** `django_apps.asteroid_lab.optimization/` resurrection. TDD gates in PR-1 before solver depth. PR sequence: **PR-1** skeleton → **PR-2** L2 → **PR-3a** candidate/probe contracts → **PR-3b** L3/L4 generators → **PR-4** L5 + entry.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy `django_apps config src`, `StrEnum`, `dataclasses`, `Decimal`

**Spec:** [`2026-05-27-asteroid-lab-algorithm-layer-stack-design.md`](../specs/2026-05-27-asteroid-lab-algorithm-layer-stack-design.md)

**Branch:** `feat/asteroid-lab-layer-stack` (dedicated worktree recommended)

---

## File map (summary)

| Action | Path |
|--------|------|
| Create | `django_apps/asteroid_lab/layers/**` |
| Create | `django_apps/asteroid_lab/layers/layer_01_reconstruction/run.py` |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_entry.py` (PR-4) |
| Modify | `config/settings.py` — `ASTEROID_LAB_LAYER_STACK_ENABLED = False` (PR-4) |
| Create | `tests/unit/asteroid_lab/layers/**` |
| Create | `documents/Algorithm/asteroid_lab_13_layer_stack.md` |
| Modify | `documents/index/document_inventory.md`, `documents/Algorithm/README.md`, `structure.md` |
| Modify | `documents/ai/current_plan.md` (ACTIVE queue row) |

### Forbidden (normative — narrow scope)

```text
CREATE or IMPORT django_apps/asteroid_lab/optimization/ (package must stay absent)
IMPORT django_apps.asteroid_lab.optimization or .catalog from layers/**
IMPORT deleted/frozen asteroid_lab optimization DTO/runtime as L2–L5 dependency
placement_stack as identifier/path segment under django_apps/asteroid_lab/** (runtime hard fail)
layer_06_* packages or registration in stack_runner
resumable diagnostic APIs (resume_from_diagnostic, run_from_layer_N, etc.)
```

**Not forbidden globally:** historical docs mentioning `optimization/`; other apps; governance docs that *describe* forbidden tokens (see token gate policy below).

**Feature flag:** `ASTEROID_LAB_LAYER_STACK_ENABLED` default **False** in settings. Tests use `@override_settings` only — **no environment-variable implicit enable.**

---

## Task 0: Docs alignment (P0)

**Files:**
- Create: `documents/Algorithm/asteroid_lab_13_layer_stack.md`
- Modify: `documents/Algorithm/README.md`, `documents/index/document_inventory.md`, `structure.md`, `documents/ai/current_plan.md`

- [ ] **Step 1: Create `asteroid_lab_13_layer_stack.md`** — L1–L6 table, facade note, link to spec/plan.

- [ ] **Step 2: Update inventory + README + structure.**

- [ ] **Step 3: `current_plan.md`** — ACTIVE row for layer stack plan; RTTP rows stay BLOCKED.

- [ ] **Step 4: Commit (docs-only)** — when user requests commit.

---

## PR-1 — Stack skeleton + contracts + gates

### Task 1: Layer contracts module

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/stack_status.py`
- Create: `django_apps/asteroid_lab/layers/contracts/layer_budget.py`
- Create: `django_apps/asteroid_lab/layers/contracts/diagnostic.py`
- Create: `django_apps/asteroid_lab/layers/contracts/stack_result.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_contracts.py`

- [ ] **Step 1: Write failing tests (deterministic clock)**

```python
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.stack_status import StackRunStatus


def test_stack_run_status_values() -> None:
    assert StackRunStatus.SUCCESS.value == "success"
    assert StackRunStatus.TIMEOUT_FAIL_CLOSED.value == "timeout_fail_closed"


def test_layer_budget_context_remaining_ms() -> None:
    ctx = LayerBudgetContext(
        deadline_monotonic=1000.0,
        started_monotonic=940.0,
        now_fn=lambda: 940.0,
    )
    assert ctx.remaining_budget_ms() == 60_000


def test_layer_budget_context_exhausted_returns_zero() -> None:
    ctx = LayerBudgetContext(
        deadline_monotonic=1000.0,
        started_monotonic=940.0,
        now_fn=lambda: 1001.0,
    )
    assert ctx.remaining_budget_ms() == 0


def test_layer_budget_context_from_budget_ms() -> None:
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 100.0)
    assert ctx.started_monotonic == 100.0
    assert ctx.deadline_monotonic == 160.0
    assert ctx.remaining_budget_ms() == 60_000
```

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_contracts.py -v
```

- [ ] **Step 3: Implement contracts**

```python
# layer_budget.py
from collections.abc import Callable
from dataclasses import dataclass
import time


@dataclass(frozen=True, slots=True)
class LayerBudgetContext:
    deadline_monotonic: float
    started_monotonic: float
    now_fn: Callable[[], float] = time.monotonic

    @classmethod
    def from_budget_ms(
        cls,
        budget_ms: int,
        *,
        now_fn: Callable[[], float] = time.monotonic,
    ) -> LayerBudgetContext:
        started = now_fn()
        return cls(
            deadline_monotonic=started + budget_ms / 1000,
            started_monotonic=started,
            now_fn=now_fn,
        )

    def remaining_budget_ms(self) -> int:
        return max(0, int((self.deadline_monotonic - self.now_fn()) * 1000))
```

```python
# stack_result.py
@dataclass(frozen=True, slots=True)
class StackRunResult:
    status: StackRunStatus
    completed_layer_slugs: tuple[str, ...]
    failed_layer_slug: str | None
    diagnostic_snapshot: DiagnosticLayerSnapshot | None
```

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: ruff**

```powershell
python -m ruff check django_apps/asteroid_lab/layers tests/unit/asteroid_lab/layers
```

**Task 1 checklist:**

```text
[ ] now_fn injection on LayerBudgetContext
[ ] from_budget_ms constructor
[ ] deterministic remaining_budget_ms test
[ ] exhausted budget returns 0
```

---

### Task 2: Layer-01 facade

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_01_reconstruction/run.py`, `output.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_01_facade.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_import_matrix.py`

- [ ] **Step 1: Failing test `test_run_layer_01_returns_layer01_output`** — use `tests/support/reconstruction_complete_map_fixtures.py` where possible.

- [ ] **Step 2: Implement `run_layer_01`** — delegate to existing reconstruction + capacity builders.

- [ ] **Step 3: AST gate — `reconstruction/` does not import `asteroid_lab.layers`.**

- [ ] **Step 4: AST gate — `layers/**` does not import `django_apps.asteroid_lab.optimization`**

```python
def test_layers_do_not_import_asteroid_lab_optimization() -> None:
    root = Path("django_apps/asteroid_lab/layers")
    forbidden = "django_apps.asteroid_lab.optimization"
    # walk Import/ImportFrom only under layers/
```

---

### Task 3: stack_runner skeleton

**Files:**
- Create: `django_apps/asteroid_lab/layers/stack_runner.py`
- Create stub `layer_02` … `layer_05` `run.py` (raise `NotImplementedError` or return empty until later PRs)
- Test: `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py`
- Test: `tests/unit/asteroid_lab/layers/test_placement_stack_token_policy.py`
- Test: `tests/unit/asteroid_lab/layers/test_diagnostic_snapshot_not_resumable.py`

- [ ] **Step 1: Failing tests**

```python
def test_stack_runner_invokes_l1_then_l2_to_l5() -> None:
    ...

def test_l6_not_registered_in_stack_runner_source() -> None:
    source = Path("django_apps/asteroid_lab/layers/stack_runner.py").read_text(encoding="utf-8")
    assert "layer_06" not in source
    assert "floor2_space_link" not in source


def test_no_layer_06_package_exists() -> None:
    root = Path("django_apps/asteroid_lab/layers")
    assert not any("layer_06" in p.name for p in root.rglob("*"))


def test_remaining_budget_zero_skips_layer_without_call() -> None:
    # inject now_fn so budget exhausted before layer_03; assert layer_03 run not called (mock)


def test_stack_runner_timeout_records_failed_layer_slug() -> None:
    result = run_layers_02_to_05(..., budget exhausted mid-run)
    assert result.status == StackRunStatus.TIMEOUT_FAIL_CLOSED
    assert result.failed_layer_slug == "layer_03_rim_mining_bundles"  # example
```

**Token gate policy (안 A — normative):**

| Scope | Policy |
|-------|--------|
| `django_apps/asteroid_lab/**/*.py` | **Hard fail** if `placement_stack` appears as substring in source (identifier/path) |
| `documents/ai/current_plan.md` | **Hard fail** same |
| `docs/superpowers/specs/**` | **Do not scan** in PR-1 gate (governance docs describe forbidden tokens) |

```python
def test_placement_stack_token_forbidden_in_runtime_code() -> None:
    roots = [Path("django_apps/asteroid_lab")]
    token = "placement_stack"
    for path in roots[0].rglob("*.py"):
        if token in path.read_text(encoding="utf-8"):
            raise AssertionError(path)


def test_placement_stack_token_limited_to_governance_docs() -> None:
    """Optional doc test: specs may mention token; runtime may not."""
    ...
```

- [ ] **Step 2: Implement `run_full` / `run_layers_02_to_05`**

- On `remaining_budget_ms <= 0` before layer N: return `StackRunResult(TIMEOUT_FAIL_CLOSED, failed_layer_slug=<slug of layer that would have run>, ...)`.

- [ ] **Step 3: Non-resumable API gate** — no `resume`, `from_diagnostic`, `run_from_layer` in `stack_runner` public names (`dir()` / AST).

- [ ] **Step 4: pytest + ruff**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/ -v
```

**Task 3 checklist:**

```text
[ ] Token gate: runtime hard fail; specs not scanned
[ ] No layer_06 package under layers/
[ ] Zero budget skips next layer without invoke
[ ] Timeout sets failed_layer_slug
```

---

## PR-2 — Layer-2 exterior transport

### Task 4: ExteriorConnectionPlan DTO + EVTC

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_02_exterior_transport/plan.py`, `run.py`
- Create: `django_apps/asteroid_lab/layers/shared/ceildiv.py` (integer-only)
- Test: `tests/unit/asteroid_lab/layers/test_layer_02_exterior_connection_plan.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_02_evtc_no_literals.py`

- [ ] **Step 1: Failing tests**

```python
from decimal import Decimal


def ceildiv_decimal(n: Decimal, d: Decimal) -> int:
  """Use integer mini-units or quantize to int before ceildiv — no float ceil."""
  ...


def test_required_connectors_uses_integer_ceildiv(db) -> None:
    plan = build_exterior_connection_plan(..., throughput_target_percent=80)
    # planning_target and per_connector as Decimal; convert to int mini-units for count
    assert plan.required_connector_count == expected_int_ceildiv


def test_throughput_target_percent_bounds_delegated(db) -> None:
    # invalid percent rejected upstream OR layer asserts via throughput_target.parse
    ...


def test_l2_fails_closed_on_missing_evtc_capacity(db) -> None:
    # LookupError from EVTC → layer returns failure; stack maps to LAYER_FAILED_CLOSED
    # no uncaught LookupError to caller
```

- [ ] **Step 2: Implement L2** — EVTC service only; missing row → structured `unmet_reason` / stack `LAYER_FAILED_CLOSED`.

- [ ] **Step 3: Literal gate on `layer_02_exterior_transport/`**

- [ ] **Step 4: Wire stack_runner layer 2 slot**

**Task 4 checklist:**

```text
[ ] Decimal throughput_target_percent (no float ceil on rates)
[ ] Percent 10–80 asserted or delegated with explicit test
[ ] Missing EVTC → LAYER_FAILED_CLOSED, not raw exception
```

---

## PR-3a — Candidate / probe contracts (no rim/inner generators yet)

### Task 5a: shared contracts + probe + pattern_library core

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/candidates.py`
- Create: `django_apps/asteroid_lab/layers/shared/pattern_library.py`
- Create: `django_apps/asteroid_lab/layers/shared/route_probe.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py`

- [ ] **Step 1: Fix `RouteProbeStatus` + `CandidateRejectReason` StrEnums before generators**

```python
class CandidateRejectReason(StrEnum):
    ROUTE_PROBE_FAILED = "route_probe_failed"
    UNPROBED = "unprobed"
    BUDGET_EXHAUSTED = "budget_exhausted"
    ...
```

- [ ] **Step 2: Failing pool invariant tests**

```python
def test_normal_candidates_type_requires_succeeded_status() -> None:
    # factory/helper that refuses to build RimBundleCandidateSet with FAILED in normal_candidates
    ...

def test_unprobed_candidate_never_enters_normal_pool() -> None:
    ...

def test_route_probe_failed_goes_to_diagnostic_rejected_only() -> None:
    ...
```

- [ ] **Step 3: Minimal `pattern_library` + `route_probe` stubs** — enough for tests; no L3/L4 `run.py` yet.

- [ ] **Step 4: pytest PR-3a only**

```powershell
python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_04_probe_before_pool.py -v
```

**PR-3a commit boundary:** contracts + shared + pool tests green; **no** `layer_03`/`layer_04` generators.

---

## PR-3b — L3 rim + L4 inner generators

### Task 5b: layer_03 + layer_04 + stack slots + budget loops

**Files:**
- Create: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/run.py`
- Create: `django_apps/asteroid_lab/layers/layer_04_inner_pattern_fill/run.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_04_inner_fill.py`
- Test: `tests/unit/asteroid_lab/layers/test_stack_runner_budget_interruption.py`

- [ ] **Step 1: L3 rim generator** — 1-line / L-shape bundles; no outer-rim greedy recurrence.

- [ ] **Step 2: L4 inner fill** — remaining mineable via `pattern_library`.

- [ ] **Step 3: Budget checks inside probe loops** — honor `remaining_budget_ms`; emit `RouteProbeStatus.SKIPPED_BUDGET` → diagnostic bucket.

- [ ] **Step 4: Wire layers 3–4 in `stack_runner`**

- [ ] **Step 5: Commit PR-3b separately from PR-3a** (two commits or two PRs to same branch).

---

## PR-4 — Layer-5 commit_validate + solver entry

### Task 6: L5 subphases

**Files:**
- `layer_05_commit_validate/commit.py` (L5a), `validate.py` (L5b), `summary.py` (L5c)
- Test: `tests/unit/asteroid_lab/layers/test_layer_05_subphases_read_only.py`

- [ ] **Step 1: AST import gate on `validate.py`**

```python
import ast
from pathlib import Path

FORBIDDEN_VALIDATE_IMPORT_SUBSTRINGS = (
    "route_probe",
    "layer_05_commit_validate.commit",
)


def test_validation_does_not_import_route_probe() -> None:
    path = Path("django_apps/asteroid_lab/layers/layer_05_commit_validate/validate.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "route_probe" not in node.module
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "route_probe" not in alias.name
```

- [ ] **Step 2: `test_validation_does_not_mutate_committed_set`** — frozen input copy / deep equality before-after `run_validation`.

- [ ] **Step 3: `test_summary_projection_does_not_change_validation_result`** — deep equality on `ValidationResult`.

- [ ] **Step 4: `test_commit_reprobes_latest_domain`** — stub proves candidate-stage probe result ignored when commit reprobe disagrees.

- [ ] **Step 5: Implement L5a/b/c**

**Task 6 checklist:**

```text
[ ] validate.py AST import gate (not substring file read)
[ ] validation no-mutation test
[ ] summary projection deep equality
[ ] commit-time reprobe overrides candidate-stage probe
```

---

### Task 7: solver_runtime_entry wiring

**Files:**
- Modify: `config/settings.py`, `solver_runtime_entry.py`
- Test: `tests/unit/asteroid_lab/test_solver_runtime_entry_layer_stack.py`

- [ ] **Step 1: Add `ASTEROID_LAB_LAYER_STACK_ENABLED = False` in settings**

```text
Default production: reconstruction-only / SOLVER_NOT_AVAILABLE until PR-4 gates green.
Unit tests: @override_settings(ASTEROID_LAB_LAYER_STACK_ENABLED=True) only.
No os.environ read for enable.
```

- [ ] **Step 2: Wire `stack_runner.run_full` when flag True**

- [ ] **Step 3: Map `TIMEOUT_FAIL_CLOSED` → `SolverRuntimeEntryErrorCode.SOLVER_TIME_BUDGET_EXCEEDED`**

- [ ] **Step 4: Assert HTTP 200 + `ok: false` + `stack_run_status` in solver_summary on timeout**

```python
@pytest.mark.django_db
@override_settings(ASTEROID_LAB_LAYER_STACK_ENABLED=True)
def test_solver_entry_timeout_returns_ok_false_and_status(client) -> None:
    ...
    assert response.status_code == 200
    assert body["ok"] is False
    assert body["solver_summary"]["stack_run_status"] == "timeout_fail_closed"
```

- [ ] **Step 5: Narrow pytest + ruff**

**Task 7 checklist:**

```text
[ ] Feature flag default off
[ ] override_settings in tests only
[ ] No env-var implicit enable
[ ] timeout → SOLVER_TIME_BUDGET_EXCEEDED
[ ] HTTP 200 + ok:false asserted
[ ] solver_summary includes stack_run_status
```

---

## Contract checklist (PR-4 body)

Copy spec §8; all boxes checked before default-on flag or removing `SOLVER_NOT_AVAILABLE` default.

---

## Verification (before merge)

```powershell
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m mypy django_apps config src
python -m black --check .
```

---

## Plan self-review (patched)

| Review item | Addressed in |
|-------------|----------------|
| Budget clock injection | Task 1 |
| Token scan allowlist | Task 3 policy table |
| optimization scope | Forbidden section + Task 2 import gate |
| PR-3 split | Task 5a / 5b |
| StackRunResult fields | Task 1 + Task 3 |
| layer_06 package gate | Task 3 |
| L5 AST validation gate | Task 6 |
| Feature flag policy | Task 7 |

---

## Execution handoff

**Status:** Ready to execute PR-1 after user confirms.

1. **Subagent-Driven (recommended)** — PR-1 → PR-2 → PR-3a → PR-3b → PR-4  
2. **Inline Execution** — same sequence in this session  

Which approach?
