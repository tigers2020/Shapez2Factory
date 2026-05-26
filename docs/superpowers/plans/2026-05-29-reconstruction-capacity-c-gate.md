# Reconstruction Capacity C-GATE — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lock `ReconstructionCompleteMap` as the sole terrain SoT for capacity, mineable, and `OptimizationInput` via architecture gates and Lab summary contract tests — **no solver behaviour change** on PR-CGATE-1.

**Architecture:** Single architecture test module (G1 import + G2 semantic token gates) mirrors PR-B; extend existing complete-map regression tests (G3); add canon-derived Lab summary contract test (G4); standing PowerShell script (G5); governance rows in `current_plan.md` and roadmap. Production observability renames stay in optional PR-CGATE-1b only if gates fail without them.

**Tech Stack:** Python 3.12+, `ast`, pytest, ruff, PowerShell (`scripts/test_capacity_sot.ps1`)

**Spec:** [`../specs/2026-05-29-reconstruction-capacity-c-gate-design.md`](../specs/2026-05-29-reconstruction-capacity-c-gate-design.md)

**Branch:** `feat/reconstruction-capacity-c-gate` (dedicated worktree recommended)

**PR-CGATE-1 scope:** docs + tests + script + governance only (default). **PR-CGATE-1b:** observability/Lab mapping only — separate PR if Task 7 shows red on master without 1b.

---

## File map

| File | Action | Responsibility |
|------|--------|----------------|
| `tests/unit/architecture/test_capacity_complete_map_sot_gates.py` | Create | G1 AST import + G2 semantic token PASS authority |
| `tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py` | Modify | G3 canon capacity platform == `shape_field_cell_count` |
| `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` | Modify | G4 `test_lab_capacity_uses_complete_map_even_when_overlay_is_sparse` |
| `scripts/test_capacity_sot.ps1` | Create | G5 standing narrow gate |
| `documents/ai/current_plan.md` | Modify | ACTIVE → CLOSED, Maintenance gate owner |
| `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | Modify | Axis A ACTIVE pointer |
| `docs/superpowers/specs/2026-05-29-reconstruction-capacity-c-gate-design.md` | Modify (optional) | Status line → `Design approved; implementation plan pending` |

**No production changes expected** on current `master` for PR-CGATE-1.

**G1 scan note:** `reconstruction_capacity_summary.py` is scanned by G1 (forbidden overlay imports) but **excluded from G2** token scan — it is the complete-map envelope authority (spec §5 G2).

---

## Task 0: Preflight on `master`

**Files:** none (verification only)

- [ ] **Step 1: Confirm complete-map SoT already present**

```powershell
Test-Path django_apps/asteroid_lab/reconstruction/complete_map.py
Test-Path tests/unit/asteroid_lab/test_complete_map.py
```

Expected: both `True`

- [ ] **Step 2: Confirm overlay helpers not imported from optimization**

```powershell
rg "mineable_coords_from_reconstruction|acceptance_topology_from_reconstruction|asteroid_field_cells_from_reconstruction" django_apps/asteroid_lab/optimization --glob "*.py"
```

Expected: no matches (empty)

- [ ] **Step 3: Run existing complete-map regression (baseline green)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_complete_map.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py tests/unit/asteroid_lab/test_optimization_input_adapter.py -k "mineable_cells == complete or overlay_field or complete_map" -v --tb=short
```

If `-k` expression is awkward, run full files:

```powershell
python -m pytest tests/unit/asteroid_lab/test_complete_map.py tests/unit/asteroid_lab/test_optimization_input_adapter.py -v --tb=short
```

Expected: PASS

- [ ] **Step 4: Create branch**

```powershell
git checkout -b feat/reconstruction-capacity-c-gate
```

---

## Task 1: G1 — AST import guard (failing test first)

**Files:**

- Create: `tests/unit/architecture/test_capacity_complete_map_sot_gates.py`
- Test: same file

- [ ] **Step 1: Add failing import-gate test skeleton**

Create `tests/unit/architecture/test_capacity_complete_map_sot_gates.py`:

```python
"""Capacity C-GATE — complete-map SoT architecture gates (G1 + G2).

Spec: docs/superpowers/specs/2026-05-29-reconstruction-capacity-c-gate-design.md
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LAB_ROOT = _REPO_ROOT / "django_apps" / "asteroid_lab"

_FORBIDDEN_SYMBOLS: frozenset[str] = frozenset(
    {
        "mineable_coords_from_reconstruction",
        "external_void_coords_from_reconstruction",
        "asteroid_field_cells_from_reconstruction",
    }
)

_G1_SCAN_REL_PATHS: tuple[str, ...] = (
    "optimization",
    "services/solver_runtime_entry.py",
    "services/reconstruction_capacity_summary.py",
)


def _g1_py_files() -> list[Path]:
    out: list[Path] = []
    for rel in _G1_SCAN_REL_PATHS:
        path = _LAB_ROOT / rel
        if path.is_file():
            out.append(path)
            continue
        out.extend(sorted(path.rglob("*.py")))
    return out


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def _rel(path: Path) -> str:
    return path.relative_to(_LAB_ROOT).as_posix()


def _imported_names(tree: ast.Module) -> list[tuple[str, int]]:
    names: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.append((alias.name, node.lineno))
    return names


def _forbidden_calls(tree: ast.Module) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "acceptance_topology_from_reconstruction":
                hits.append(f"L{node.lineno}: call acceptance_topology_from_reconstruction")
    return hits


def test_g1_no_overlay_mineable_imports_in_scanned_roots() -> None:
    violations: list[str] = []
    for path in _g1_py_files():
        tree = _parse(path)
        rel = _rel(path)
        for name, lineno in _imported_names(tree):
            if name in _FORBIDDEN_SYMBOLS:
                violations.append(f"{rel}:{lineno}: imports forbidden symbol {name!r}")
        for hit in _forbidden_calls(tree):
            violations.append(f"{rel}:{hit}")
    assert not violations, "\n".join(violations)
```

- [ ] **Step 2: Run G1 test — expect PASS on current master**

```powershell
python -m pytest tests/unit/architecture/test_capacity_complete_map_sot_gates.py::test_g1_no_overlay_mineable_imports_in_scanned_roots -v --tb=short
```

Expected: PASS (optimization already clean). If FAIL, fix production imports in same PR before proceeding — **do not weaken the gate**.

- [ ] **Step 3: Commit (optional — user-requested commits only)**

```powershell
git add tests/unit/architecture/test_capacity_complete_map_sot_gates.py
git commit -m "test(asteroid_lab): add capacity complete-map G1 import gate"
```

---

## Task 2: G2 — Semantic token gate

**Files:**

- Modify: `tests/unit/architecture/test_capacity_complete_map_sot_gates.py`

- [ ] **Step 1: Add constants and file collectors for G2**

Append to `test_capacity_complete_map_sot_gates.py`:

```python
_DECISION_SUBDIRS: frozenset[str] = frozenset(
    {
        "commit",
        "selection",
        "routing",
        "candidates",
        "validation",
        "macros",
        "skeleton",
    }
)

_G2_EXCLUDED_REL: frozenset[str] = frozenset(
    {
        "optimization/pipeline.py",
        "optimization/rttp_solver_summary.py",
        "optimization/rttp_replay_diagnostics.py",
        "optimization/replay_sink.py",
        "services/reconstruction_capacity_summary.py",
    }
)

_FORBIDDEN_CALLEE_SUBSTRINGS: frozenset[str] = frozenset(
    {
        "mineable",
        "field_cell",
        "capacity",
        "platform_count",
    }
)

_RECON_RESULT_PARAM_NAMES: frozenset[str] = frozenset({"recon", "result", "reconstruction"})


def _g2_scan_files() -> list[Path]:
    opt = _LAB_ROOT / "optimization"
    out: list[Path] = []
    for sub in sorted(_DECISION_SUBDIRS):
        root = opt / sub
        if root.is_dir():
            out.extend(sorted(root.rglob("*.py")))
    for rel in (
        "optimization/reconstruction_adapter.py",
        "services/solver_runtime_entry.py",
    ):
        path = _LAB_ROOT / rel
        if path.is_file():
            out.append(path)
    filtered: list[Path] = []
    for path in out:
        if _rel(path) in _G2_EXCLUDED_REL:
            continue
        filtered.append(path)
    return filtered


def _is_recon_cells(node: ast.AST, param_names: frozenset[str]) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "cells"
        and isinstance(node.value, ast.Name)
        and node.value.id in param_names
    )


def _forbidden_recon_cells_usage(tree: ast.Module, *, rel: str) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
            for tgt in targets:
                if isinstance(tgt, ast.Name) and tgt.id == "mineable_cells":
                    if _is_recon_cells(value, _RECON_RESULT_PARAM_NAMES) or (
                        isinstance(value, ast.Call)
                        and isinstance(value.func, ast.Name)
                        and any(s in value.func.id for s in _FORBIDDEN_CALLEE_SUBSTRINGS)
                    ):
                        hits.append(
                            f"{rel}:L{node.lineno}: mineable_cells assigned from overlay path"
                        )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if any(s in node.func.id for s in _FORBIDDEN_CALLEE_SUBSTRINGS):
                for arg in node.args:
                    if _is_recon_cells(arg, _RECON_RESULT_PARAM_NAMES):
                        hits.append(
                            f"{rel}:L{node.lineno}: recon.cells passed to {node.func.id}"
                        )
    return hits


def test_g2_no_overlay_cells_on_decision_capacity_paths() -> None:
    violations: list[str] = []
    for path in _g2_scan_files():
        rel = _rel(path)
        tree = _parse(path)
        violations.extend(_forbidden_recon_cells_usage(tree, rel=rel))
    assert not violations, "\n".join(violations)
```

- [ ] **Step 2: Run G2 test**

```powershell
python -m pytest tests/unit/architecture/test_capacity_complete_map_sot_gates.py::test_g2_no_overlay_cells_on_decision_capacity_paths -v --tb=short
```

Expected: PASS on current `master`. If FAIL, inspect violation path:
- If legitimate complete-map path → refine heuristic (same PR, spec amendment if allowlist grows).
- If real overlay SoT regression → fix production in PR-CGATE-1 only if minimal; else document for 1b.

- [ ] **Step 3: Run full architecture gate module**

```powershell
python -m pytest tests/unit/architecture/test_capacity_complete_map_sot_gates.py -v --tb=short
```

Expected: 2 passed

---

## Task 3: G3 — Canon capacity regression extension

**Files:**

- Modify: `tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py`

- [ ] **Step 1: Add canon fixture helper and failing test**

Append imports at top of `test_reconstruction_capacity_summary.py` (if not present):

```python
from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.complete_map import (
    build_reconstruction_complete_map,
    overlay_field_cell_count,
)
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
```

Append test:

```python
def _canon_cleanup_recon_complete():
    required_copy, _solved = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    return recon, complete


def test_canon_capacity_platform_count_matches_complete_map_shape_fields() -> None:
    recon, complete = _canon_cleanup_recon_complete()
    row = build_reconstruction_capacity_summary(complete_map=complete, resource_kind="shape")
    assert row["capacity_upper_bound_platform_count"] == complete.shape_field_cell_count
    assert overlay_field_cell_count(recon) < len(complete.field_cells)
```

- [ ] **Step 2: Run new test**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py::test_canon_capacity_platform_count_matches_complete_map_shape_fields -v --tb=short
```

Expected: PASS

- [ ] **Step 3: Run G3 file bundle**

```powershell
python -m pytest tests/unit/asteroid_lab/test_complete_map.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py -v --tb=short
```

Expected: all PASS

---

## Task 4: G4 — Lab summary contract test

**Files:**

- Modify: `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`

- [ ] **Step 1: Add required test (canon-derived observability + capacity)**

Append to `tests/unit/asteroid_lab/test_solver_run_lab_summary.py`:

```python
from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.complete_map import (
    build_reconstruction_complete_map,
    overlay_field_cell_count,
)
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
    build_reconstruction_observability,
)


def test_lab_capacity_uses_complete_map_even_when_overlay_is_sparse() -> None:
    required_copy, _solved = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)

    obs = build_reconstruction_observability(recon=recon, complete_map=complete)
    cap = build_reconstruction_capacity_envelope(complete_map=complete)

    overlay_cells = len(recon.cells)
    display_cells = len(complete.cells)
    overlay_fields = overlay_field_cell_count(recon)
    complete_fields = len(complete.field_cells)
    shape_platform = cap["by_resource"]["shape"]["capacity_upper_bound_platform_count"]

    assert overlay_cells != display_cells
    assert overlay_fields < complete_fields
    assert shape_platform == complete.shape_field_cell_count
    assert shape_platform != overlay_fields

    row = lab_run_summary_from_solver_summary(
        run_id=1,
        status="completed",
        solver_summary={
            "validation_passed": True,
            "confirmed_count": 0,
            "reconstruction_observability": obs,
            "reconstruction_capacity": cap,
        },
    )
    assert row["capacity"]["platform_upper_bound"] == shape_platform
    assert row["reconstruction"]["asteroid_field_cell_count"] == complete_fields
    assert row["reconstruction"]["shape_field_cell_count"] == complete.shape_field_cell_count
```

- [ ] **Step 2: Run G4 test**

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py::test_lab_capacity_uses_complete_map_even_when_overlay_is_sparse -v --tb=short
```

Expected: PASS

**Forbidden:** Do not add `assert cell_count != platform_upper_bound` as the only drift check.

---

## Task 5: G5 — Standing script

**Files:**

- Create: `scripts/test_capacity_sot.ps1`

- [ ] **Step 1: Create script**

Create `scripts/test_capacity_sot.ps1`:

```powershell
# Capacity C-GATE standing gate — complete-map SoT (see documents/ai/current_plan.md).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

python -m pytest tests/unit/architecture/test_capacity_complete_map_sot_gates.py -v --tb=short @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m pytest tests/unit/asteroid_lab/test_complete_map.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py -v --tb=short @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py -k "complete_map_even_when_overlay_is_sparse" -v --tb=short @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m ruff check django_apps/asteroid_lab/reconstruction django_apps/asteroid_lab/services/reconstruction_capacity_summary.py tests/unit/architecture/test_capacity_complete_map_sot_gates.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

- [ ] **Step 2: Run standing gate end-to-end**

```powershell
powershell -File scripts/test_capacity_sot.ps1
```

Expected: exit 0

---

## Task 6: Governance — `current_plan.md` + roadmap

**Files:**

- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`
- Modify (optional): `docs/superpowers/specs/2026-05-29-reconstruction-capacity-c-gate-design.md` (status line only)

- [ ] **Step 1: Replace Next focus ACTIVE row**

In `documents/ai/current_plan.md` § Next focus, replace the v0.1 track-selection line with:

```markdown
**ACTIVE:** Capacity C-GATE — complete-map SoT architecture gates
- Spec: [`docs/superpowers/specs/2026-05-29-reconstruction-capacity-c-gate-design.md`](../../docs/superpowers/specs/2026-05-29-reconstruction-capacity-c-gate-design.md)
- Plan: [`docs/superpowers/plans/2026-05-29-reconstruction-capacity-c-gate.md`](../../docs/superpowers/plans/2026-05-29-reconstruction-capacity-c-gate.md)
- Blocks: GA promotion until CLOSED (new GA spec still required after C-GATE)
- Standing gate: `powershell -File scripts/test_capacity_sot.ps1`
- PR-CGATE-1: docs + tests + script only (no solver semantics)
```

- [ ] **Step 2: Add Maintenance standing gate bullet**

Under `## Maintenance / Standing Gates`, append:

```markdown
- **Capacity C-GATE (complete-map SoT) gate owner:** `powershell -File scripts/test_capacity_sot.ps1`
  - Architecture: `test_capacity_complete_map_sot_gates.py` (G1 import + G2 semantic token)
  - **Not** included in `test_reconstruction_narrow.ps1` or `test_optimization_contamination.ps1`
```

- [ ] **Step 3: Update roadmap Axis A open next**

In `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`, update the Axis A “Open next” table row to:

```text
ACTIVE: Capacity C-GATE (spec/plan 2026-05-29)
GA: blocked until C-GATE CLOSED
Macro: PAUSED (unchanged)
```

- [ ] **Step 4 (optional): Spec status line**

Change spec header status to:

```markdown
**Status:** Design approved; implementation plan pending
```

---

## Task 7: Narrow verification + closure checklist

**Files:** none (verification)

- [ ] **Step 1: Capacity C-GATE standing gate**

```powershell
powershell -File scripts/test_capacity_sot.ps1
```

Expected: exit 0

- [ ] **Step 2: Adjacent standing gates (PR merge)**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
```

Expected: exit 0 / all pass

- [ ] **Step 3: Ruff on new architecture test**

```powershell
python -m ruff check tests/unit/architecture/test_capacity_complete_map_sot_gates.py
```

Expected: All checks passed

- [ ] **Step 4: Self-review against spec**

| Spec section | Plan task |
|--------------|-----------|
| §1 scope (no solver change) | PR-CGATE-1 file map |
| §3 forbidden/allowed | G1 + G2 |
| §4 observability vocabulary | G4 + optional 1b appendix |
| §5 G1–G5 | Tasks 1–5 |
| §6 1b fallback | Appendix A |
| §7 verification | Task 7 |
| §8 governance | Task 6 |

- [ ] **Step 5: Mark CLOSED in `current_plan.md` after PR merge**

Add **CLOSED (YYYY-MM-DD):** Capacity C-GATE — PR #N, commit hash; GA promotion unblocked (spec still required).

---

## Appendix A — PR-CGATE-1b (only if Task 7 Step 1 fails without production edits)

**Trigger:** G2 or G4 red on `master` due to observability key drift only — **not** for new overlay imports in optimization (fix those in PR-CGATE-1 without weakening gates).

**Files:**

- Modify: `django_apps/asteroid_lab/services/reconstruction_capacity_summary.py`
- Modify: `django_apps/asteroid_lab/optimization/rttp_solver_summary.py`
- Modify: `django_apps/asteroid_lab/services/solver_run_lab_summary.py`

- [ ] **Step 1: Emit `overlay_cell_count` alongside deprecated `cell_count`**

In `build_reconstruction_observability`:

```python
    obs: dict[str, Any] = {
        "overlay_cell_count": len(recon.cells),
        "cell_count": len(recon.cells),  # deprecated alias
        "display_cell_count": len(complete_map.cells),
        ...
    }
```

In `reconstruction_step_from_result` metrics: add `"overlay_cell_count": len(recon.cells)` (keep `cell_count`).

- [ ] **Step 2: Lab mapper prefers `overlay_cell_count`**

In `_section_reconstruction`, map:

```python
        "cell_count": obs.get("overlay_cell_count", obs.get("cell_count", _PLACEHOLDER)),
```

Add optional key `"overlay_cell_count"` to `keys` tuple for forward compatibility.

- [ ] **Step 3: Re-run standing gate**

```powershell
powershell -File scripts/test_capacity_sot.ps1
```

**Constraints:** No changes to `reconstruction_adapter`, commit, validation, FOT, or `OptimizationInput` mineable derivation.

---

## Plan self-review (author checklist)

| Check | Result |
|-------|--------|
| Spec §1–§9 each mapped to a task | Tasks 0–7 + Appendix A |
| No TBD / “implement later” steps | Concrete code in Tasks 1–4 |
| G2 excludes `reconstruction_capacity_summary.py` | Task 2 + file map note |
| G4 uses inequality chain on canon fixture | Task 4 |
| PR-CGATE-1 vs 1b split | File map + Appendix A |
| Commits marked optional per repo user rule | Steps note user-requested commits |

---

## Execution handoff

Plan saved. **Do not start implementation in this review-only turn.**

When executing:

1. **Subagent-Driven (recommended)** — superpowers:subagent-driven-development, one task per subagent, review between tasks.
2. **Inline Execution** — superpowers:executing-plans, batch with checkpoints after Task 5 and Task 7.

Which approach do you want for PR-CGATE-1?
