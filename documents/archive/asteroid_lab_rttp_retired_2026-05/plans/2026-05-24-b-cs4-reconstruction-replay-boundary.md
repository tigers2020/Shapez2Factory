---
status: RETIRED_ARCHIVE
do_not_execute: true
superseded_by: docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md
---

# B-CS4 Reconstruction / Lab Replay Boundary — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Axis B milestone B-CS4 (Hybrid C) by proving reconstruction + audited Lab replay boundaries via pytest — **no production code changes** — then register standing owner `scripts/test_reconstruction_narrow.ps1`.

**Architecture:** New `test_b_cs4_reconstruction_replay_boundary.py` holds AST PASS authority (B-CS3 mirror). Existing six narrow behavioral tests remain secondary regression. Narrow script adds B-CS4 module only — **never** `test_rttp_replay_*`.

**Tech Stack:** Python 3.14, pytest, Django ORM (persist sentinel), `ast`, `unittest.mock`

**Spec:** [`docs/superpowers/specs/2026-05-24-b-cs4-reconstruction-replay-boundary-design.md`](../specs/2026-05-24-b-cs4-reconstruction-replay-boundary-design.md)

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Read | Spec (above) | B-CS4-1 … B-CS4-10 |
| Read | `docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md` | GATE-1 |
| Read | `scripts/test_reconstruction_narrow.ps1` | Standing gate owner |
| Read | `tests/unit/asteroid_lab/test_persistence_does_not_read_replay_frames.py` | Absorb sentinel pattern |
| Read | `tests/unit/asteroid_lab/test_replay_timeline_dto.py` | `_FORBIDDEN_IMPORT_FRAGMENTS` |
| Read | `tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py` | AST helper pattern |
| Create | `tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py` | Primary B-CS4 suite |
| Modify | `scripts/test_reconstruction_narrow.ps1` | Append `test_b_cs4_*` path |
| Modify | `documents/ai/current_plan.md` | B-CS4 CLOSED + Maintenance section |
| Modify | `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | B-CS4 ✅ |

**Forbidden:** `django_apps/asteroid_lab/reconstruction/**`, audited `replay/**` production edits (unless BLOCKED leak PR). **Forbidden:** add `test_rttp_replay_*` to narrow.ps1.

---

## Shared test constants (Task 1 file header)

Create `tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py`:

```python
"""B-CS4 — reconstruction / Lab replay boundary audit (Axis B).

Spec: docs/superpowers/specs/2026-05-24-b-cs4-reconstruction-replay-boundary-design.md
PASS authority: AST import guards, ReplayFrame ORM call sentinel on persist.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RECONSTRUCTION_PKG = _REPO_ROOT / "django_apps" / "asteroid_lab" / "reconstruction"
_REPLAY_PKG = _REPO_ROOT / "django_apps" / "asteroid_lab" / "replay"

_AUDITED_REPLAY_MODULES = (
    "reconstruction_frames.py",
    "snapshot_map_replay.py",
    "timeline_dtos.py",
    "timeline_serialization.py",
    "event_types.py",
    "replay_enums.py",
)

_RECONSTRUCTION_FORBIDDEN_IMPORT_PREFIXES = (
    "django_apps.asteroid_lab.optimization",
    "django_apps.shapez_solver",
)

_REPLAY_FORBIDDEN_IMPORT_PREFIXES = (
    "django_apps.asteroid_lab.optimization",
    "django_apps.asteroid_lab.services.solver_runtime_entry",
    "django_apps.asteroid_lab.services.solver_runtime_pipeline",
    "django_apps.asteroid_lab.services.lab_rttp_snapshot_compose",
    "django_apps.asteroid_lab.optimization.replay_sink",
    "django_apps.shapez_solver",
    "django_apps.shapez_core",
)

_TRACE_FORBIDDEN_IMPORT_PREFIXES = (
    "django_apps.asteroid_lab.services.solver_runtime_entry",
    "django_apps.asteroid_lab.optimization.replay_sink",
    "django_apps.asteroid_lab.services.lab_rttp_snapshot_compose",
)

_TIMELINE_DTO_FORBIDDEN_IMPORT_PREFIXES = (
    "django_apps.asteroid_lab.models",
    "django_apps.asteroid_lab.services.replay_service",
    "django_apps.asteroid_lab.services.optimization_replay_persist",
    "django_apps.asteroid_lab.services.solver_runtime_pipeline",
    "django_apps.asteroid_lab.services.solver_runtime_entry",
    "django_apps.asteroid_lab.services.runtime_replay_recorder",
)

_TIMELINE_DTO_FORBIDDEN_FRAGMENTS = _TIMELINE_DTO_FORBIDDEN_IMPORT_PREFIXES


def _forbidden_imports(path: Path, prefixes: tuple[str, ...]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                violations.extend(
                    f"{path.name}: import {alias.name}"
                    for p in prefixes
                    if alias.name == p or alias.name.startswith(p + ".")
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            violations.extend(
                f"{path.name}: from {node.module}"
                for p in prefixes
                if node.module == p or node.module.startswith(p + ".")
            )
    return violations


def _py_files_under(pkg: Path) -> list[Path]:
    return sorted(p for p in pkg.rglob("*.py") if p.is_file())
```

---

### Task 0 — Inventory (BLOCK gate)

**Files:** none (read-only)

- [ ] **Step 1: Confirm narrow gate green today**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

Expected: PASS (six modules + ruff).

- [ ] **Step 2: Confirm B-CS3 closed (no scope overlap)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py -v
```

Expected: PASS.

- [ ] **Step 3: List reconstruction modules**

```powershell
python -c "from pathlib import Path; p=Path('django_apps/asteroid_lab/reconstruction'); print(len(list(p.rglob('*.py'))))"
```

Expected: non-zero count; note count in review summary. Do not fail only because the count differs (inventory only, not a BLOCK gate).

- [ ] **Step 4: Verify no optimization imports in reconstruction (spot check)**

```powershell
python -c "import pathlib; r=pathlib.Path('django_apps/asteroid_lab/reconstruction'); print([str(x) for x in r.rglob('*.py') if 'optimization' in x.read_text(encoding='utf-8')])"
```

Expected: `[]`. If non-empty, expect B-CS4-1 to fail → **BLOCKED** for production fix PR.

---

### Task 1 — GATE-1 AST over `reconstruction/**` (B-CS4-1)

**Files:**

- Create: `tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py` (header + Task 1 test)

**Maps to spec:** B-CS4-1

- [ ] **Step 1: Write test**

```python
@pytest.mark.parametrize("module_path", _py_files_under(_RECONSTRUCTION_PKG), ids=lambda p: p.name)
def test_b_cs4_reconstruction_package_has_no_optimization_imports(module_path: Path) -> None:
    violations = _forbidden_imports(module_path, _RECONSTRUCTION_FORBIDDEN_IMPORT_PREFIXES)
    assert violations == [], "\n".join(violations)
```

- [ ] **Step 2: Run test**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py -k "reconstruction_package" -v
```

Expected: PASS. If FAIL → **BLOCKED** (separate production PR).

- [ ] **Step 3: Commit (tests only)**

```bash
git add tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py
git commit -m "test(asteroid_lab): B-CS4-1 GATE-1 reconstruction import boundary"
```

---

### Task 2 — Audited replay module AST (B-CS4-2, B-CS4-5)

**Files:**

- Modify: `tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py`

**Maps to spec:** B-CS4-2, B-CS4-5

- [ ] **Step 1: Write parametrized replay module test**

```python
@pytest.mark.parametrize("module_name", _AUDITED_REPLAY_MODULES)
def test_b_cs4_audited_replay_modules_forbidden_imports_ast(module_name: str) -> None:
    path = _REPLAY_PKG / module_name
    assert path.is_file(), f"missing audited replay module: {module_name}"
    violations = _forbidden_imports(path, _REPLAY_FORBIDDEN_IMPORT_PREFIXES)
    assert violations == [], "\n".join(violations)
```

- [ ] **Step 2: Write frame-builder no optimization adapter test**

```python
@pytest.mark.parametrize(
    "module_name",
    ("reconstruction_frames.py", "snapshot_map_replay.py"),
)
def test_b_cs4_replay_frame_builders_no_optimization_adapter_import(module_name: str) -> None:
    path = _REPLAY_PKG / module_name
    violations = _forbidden_imports(
        path,
        ("django_apps.asteroid_lab.optimization.reconstruction_adapter",)
        + _REPLAY_FORBIDDEN_IMPORT_PREFIXES,
    )
    assert violations == [], "\n".join(violations)
```

- [ ] **Step 3: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py -k "audited_replay or frame_builders" -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py
git commit -m "test(asteroid_lab): B-CS4-2/5 audited replay import boundaries"
```

---

### Task 3 — Persist ReplayFrame sentinel (B-CS4-3)

**Files:**

- Modify: `tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py`

**Maps to spec:** B-CS4-3 (PASS authority = `filter` / `get` / `all` call sentinels on `ReplayFrame.objects`)

- [ ] **Step 1: Copy fixture + test from `test_persistence_does_not_read_replay_frames.py`**

```python
from unittest.mock import MagicMock, patch

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string, encode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.services.input_service import persist_decoded_snapshot_for_map_input
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    persist_reconstructed_asteroid_map,
    run_reconstruction_for_map_input,
)


@pytest.fixture
def b_cs4_tiny_copy() -> str:
    root = {
        "V": 21,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
                {"X": 1, "Y": 1, "T": "UnknownTile_A"},
            ],
        },
    }
    return encode_copy_string(root)


@pytest.mark.django_db
def test_b_cs4_persist_does_not_invoke_replay_frame_orm_reads(b_cs4_tiny_copy: str) -> None:
    proj = m.AsteroidProject.objects.create(name="BCS4NoReplay", slug="b-cs4-no-replay-persist")
    inp = m.AsteroidMapInput.objects.create(project=proj, copy_code=b_cs4_tiny_copy)
    norm = normalize_decoded_blueprint(decode_copy_string(b_cs4_tiny_copy.removesuffix("$")))
    persist_decoded_snapshot_for_map_input(inp.id, norm)
    cleanup, recon = run_reconstruction_for_map_input(inp.id)

    with (
        patch.object(m.ReplayFrame.objects, "filter", MagicMock()) as mock_filter,
        patch.object(m.ReplayFrame.objects, "get", MagicMock()) as mock_get,
        patch.object(m.ReplayFrame.objects, "all", MagicMock()) as mock_all,
    ):
        persist_reconstructed_asteroid_map(
            map_input_id=inp.id,
            run_key="b-cs4-no-replay",
            recon=recon,
            cleanup=cleanup,
        )
        mock_filter.assert_not_called()
        mock_get.assert_not_called()
        mock_all.assert_not_called()
```

- [ ] **Step 2: Run sentinel test**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py::test_b_cs4_persist_does_not_invoke_replay_frame_orm_reads -v
```

Expected: PASS.

- [ ] **Step 3: Run legacy persistence test (must still pass)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_persistence_does_not_read_replay_frames.py -v
```

Expected: PASS (do not delete legacy test in B-CS4).

- [ ] **Step 4: Commit**

```bash
git add tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py
git commit -m "test(asteroid_lab): B-CS4-3 persist ReplayFrame ORM call sentinel"
```

---

### Task 4 — Timeline DTO boundary AST (B-CS4-4)

**Files:**

- Modify: `tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py`

**Maps to spec:** B-CS4-4

- [ ] **Step 1: Write AST test (primary)**

```python
@pytest.mark.parametrize(
    "module_name",
    ("timeline_dtos.py", "timeline_serialization.py", "replay_enums.py"),
)
def test_b_cs4_timeline_dto_modules_forbidden_imports_ast(module_name: str) -> None:
    path = _REPLAY_PKG / module_name
    violations = _forbidden_imports(
        path,
        _REPLAY_FORBIDDEN_IMPORT_PREFIXES + _TIMELINE_DTO_FORBIDDEN_IMPORT_PREFIXES,
    )
    assert violations == [], "\n".join(violations)
```

- [ ] **Step 2: Write supplementary fragment test (non-authoritative)**

```python
@pytest.mark.parametrize(
    "module_name",
    ("timeline_dtos.py", "timeline_serialization.py", "replay_enums.py"),
)
def test_b_cs4_timeline_dto_modules_supplementary_fragment_scan(module_name: str) -> None:
    text = (_REPLAY_PKG / module_name).read_text(encoding="utf-8")
    for bad in _TIMELINE_DTO_FORBIDDEN_FRAGMENTS:
        assert bad not in text, f"{module_name} must not reference {bad!r}"
```

- [ ] **Step 3: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py -k "timeline_dto" -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py
git commit -m "test(asteroid_lab): B-CS4-4 timeline DTO import boundary"
```

---

### Task 5 — Trace debug-input AST (B-CS4-6)

**Files:**

- Modify: `tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py`

**Maps to spec:** B-CS4-6

- [ ] **Step 1: Write test for `reconstruction/trace.py`**

```python
def test_b_cs4_reconstruction_trace_no_debug_algorithm_input_imports() -> None:
    path = _RECONSTRUCTION_PKG / "trace.py"
    violations = _forbidden_imports(path, _TRACE_FORBIDDEN_IMPORT_PREFIXES)
    assert violations == [], "\n".join(violations)
```

- [ ] **Step 2: Run**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py::test_b_cs4_reconstruction_trace_no_debug_algorithm_input_imports -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py
git commit -m "test(asteroid_lab): B-CS4-6 reconstruction trace input boundary"
```

---

### Task 6 — Wire narrow.ps1 (B-CS4-8)

**Files:**

- Modify: `scripts/test_reconstruction_narrow.ps1`

**Maps to spec:** B-CS4-8 (exclude `test_rttp_replay_*`)

- [ ] **Step 1: Add B-CS4 module to `$pytestPaths`**

After existing six entries, add:

```powershell
    "tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py"
```

Do **not** add any path matching `test_rttp_replay`.

- [ ] **Step 2: Run full narrow script**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

Expected: PASS (7 pytest modules + ruff).

- [ ] **Step 3: Commit**

```bash
git add scripts/test_reconstruction_narrow.ps1
git commit -m "chore(test): include B-CS4 boundary module in reconstruction narrow gate"
```

---

### Task 7 — Full B-CS4 suite + secondary behavioral (B-CS4-7)

**Files:** none (verify only)

- [ ] **Step 1: Run entire B-CS4 module**

```powershell
python -m pytest tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py -v
```

Expected: all PASS.

- [ ] **Step 2: Run legacy narrow six (without script)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py tests/unit/asteroid_lab/test_reconstruction_persist_full_map_bbox.py tests/unit/asteroid_lab/test_reconstruction_replay_merge.py tests/unit/asteroid_lab/test_island_bbox.py tests/unit/asteroid_lab/test_persistence_does_not_read_replay_frames.py tests/unit/asteroid_lab/test_replay_snapshot_contract.py -v
```

Expected: PASS.

- [ ] **Step 3: Confirm RTTP replay NOT in narrow.ps1**

```powershell
Select-String -Path scripts/test_reconstruction_narrow.ps1 -Pattern "rttp_replay"
```

Expected: no matches.

---

### Task 8 — Docs close (B-CS4-9, B-CS4-10)

**Files:**

- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`

- [ ] **Step 1: Add CLOSED entry to `current_plan.md`**

```markdown
- B-CS4 — Reconstruction / Lab replay boundary audit
  - Status: **CLOSED**
  - Spec: [`docs/superpowers/specs/2026-05-24-b-cs4-reconstruction-replay-boundary-design.md`](../../docs/superpowers/specs/2026-05-24-b-cs4-reconstruction-replay-boundary-design.md)
  - Plan: [`docs/superpowers/plans/2026-05-24-b-cs4-reconstruction-replay-boundary.md`](../../docs/superpowers/plans/2026-05-24-b-cs4-reconstruction-replay-boundary.md)
  - Evidence: `powershell -File scripts/test_reconstruction_narrow.ps1` PASS; `test_b_cs4_reconstruction_replay_boundary.py` PASS
  - PR-C: reconstruction/replay contamination portion absorbed; validation portion remains B-CS3
```

- [ ] **Step 2: Add Maintenance / Standing Gates section**

```markdown
## Maintenance / Standing Gates

- **Replay contract narrow gate owner:** `powershell -File scripts/test_reconstruction_narrow.ps1`
  - Includes B-CS4 boundary module; **excludes** `test_rttp_replay_*`
  - Failure after B-CS4 CLOSED = regression bug track (do not re-open B-CS4 ⬜ without contract change)
```

- [ ] **Step 3: Update roadmap**

In `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`:

- B-CS4 row: `✅ ongoing` → `✅` with date + spec link
- Axis B progress: B-CS1–4 formal milestones complete
- Open next: standing gate maintenance (not ⬜ milestone)
- **Next focus** table: remove B-CS4 as open; note standing owner

- [ ] **Step 4: Update spec status line**

In spec file, set:

```markdown
**Status:** CLOSED YYYY-MM-DD — evidence via `test_b_cs4_reconstruction_replay_boundary.py`
```

- [ ] **Step 5: Commit docs**

```bash
git add documents/ai/current_plan.md docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md docs/superpowers/specs/2026-05-24-b-cs4-reconstruction-replay-boundary-design.md docs/superpowers/plans/2026-05-24-b-cs4-reconstruction-replay-boundary.md
git commit -m "docs: close B-CS4 reconstruction replay boundary audit"
```

---

## Plan self-review (vs spec)

| Spec ID | Task |
|---------|------|
| B-CS4-1 | Task 1 |
| B-CS4-2 | Task 2 |
| B-CS4-3 | Task 3 |
| B-CS4-4 | Task 4 |
| B-CS4-5 | Task 2 |
| B-CS4-6 | Task 5 |
| B-CS4-7 | Task 7 |
| B-CS4-8 | Task 6 |
| B-CS4-9 | Task 8 |
| B-CS4-10 | Tasks 0–7 (no prod edits) |

| Check | Status |
|-------|--------|
| No `test_rttp_replay_*` in narrow.ps1 | Task 6 + 7 |
| Narrow replay allowlist only | Task 2 |
| Sentinel PASS for persist | Task 3 (`filter` / `get` / `all`) |
| B-CS4-4 timeline DTO AST prefixes | Task 4 (`_TIMELINE_DTO_FORBIDDEN_IMPORT_PREFIXES`) |
| RTTP scope not leaked | File map Forbidden row |
| B-CS3 pattern (AST + sentinel) | Shared constants |
| Plan review 2026-05-24 (3 corrections) | Applied |

---

## Closure command (single line for PR body)

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```
