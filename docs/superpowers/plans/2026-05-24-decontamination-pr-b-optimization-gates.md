# Decontamination PR-B — Optimization Contamination Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add AST/static contamination gates for `django_apps/asteroid_lab/optimization/` (PR-B) with no solver behaviour change.

**Architecture:** Single architecture test module enforces forbidden import prefixes, a closed per-file allowlist, and AST-based decision-path token rules; absorb and delete the legacy substring milestone test; document standing verification in `current_plan.md` and the catalog/RTTP roadmap.

**Tech Stack:** Python 3.12+, `ast`, pytest, ruff, PowerShell narrow scripts (Entry Gate A only).

**Spec:** [`../specs/2026-05-24-decontamination-pr-b-optimization-gates-design.md`](../specs/2026-05-24-decontamination-pr-b-optimization-gates-design.md)

---

## File map

| File | Action | Responsibility |
|------|--------|----------------|
| `tests/unit/architecture/test_optimization_contamination_gates.py` | Create | PR-B PASS authority (imports + tokens + closed allowlist) |
| `tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py` | Delete | Absorbed into PR-B |
| `documents/ai/current_plan.md` | Modify | Entry Gate A, PR-B ACTIVE → CLOSED, standing command |
| `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | Modify | PR-B row, open next |
| `documents/ai/contamination_policy.md` | Modify | PR-B status pointer (optional one line) |
| `scripts/test_optimization_contamination.ps1` | Create (optional) | Thin wrapper for standing gate |

**No production changes expected** on current `master` + B-CS3/4 branch tip.

---

## Task 0: Entry Gate A on `master` (precondition)

**Files:** none (verification only)

- [ ] **Step 1: Merge B-CS3/4 and checkout `master`**

```powershell
git checkout master
git pull
```

- [ ] **Step 2: Run blocking Gate 1**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

Expected: exit 0

- [ ] **Step 3: Run blocking Gate 2**

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
```

Expected: all selected tests pass

- [ ] **Step 4: Run recommended Gate 3 (non-blocking on env failure)**

```powershell
python manage.py run_solver --slug copy-import-495e552c
```

Expected: exit 0, `validation_passed` true — if DB/slug missing, record ops/env and continue PR-B

- [ ] **Step 5: Gate 4 docs sanity**

Confirm `documents/ai/current_plan.md` lists B-CS3/B-CS4 CLOSED before marking PR-B ACTIVE

---

## Task 1: PR-B test module skeleton + import gate

**Files:**

- Create: `tests/unit/architecture/test_optimization_contamination_gates.py`
- Test: same file

- [ ] **Step 1: Create test module with helpers and constants**

Create `tests/unit/architecture/test_optimization_contamination_gates.py`:

```python
"""PR-B: optimization import canon and decision-path contamination gates.

Spec: docs/superpowers/specs/2026-05-24-decontamination-pr-b-optimization-gates-design.md
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_OPTIMIZATION_ROOT = _REPO_ROOT / "django_apps" / "asteroid_lab" / "optimization"

# Closed set: only these files may import reconstruction / services / replay / adapters.
_ALLOWLIST_EXTRA: frozenset[str] = frozenset(
    {
        "reconstruction_adapter.py",
        "rttp_solver_summary.py",
        "pipeline.py",
        "replay_sink.py",
        "candidates/candidate_generator.py",
        "validation/catalog_layout_validation.py",
    }
)

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

_TOKEN_EXCLUDE_FILES: frozenset[str] = frozenset(
    {
        "pipeline.py",
        "rttp_solver_summary.py",
        "rttp_replay_diagnostics.py",
        "replay_sink.py",
        "replay_track_keys.py",
        "reconstruction_adapter.py",
        "input_contracts.py",
        "coords.py",
    }
)

_FORBIDDEN_TOKEN_IDS: frozenset[str] = frozenset(
    {
        "solver_summary",
        "ndjson",
        "ReplayFrame",
        "lab_replay_timeline",
    }
)

_SERVICE_ADAPTER_NEEDLES: frozenset[str] = frozenset(
    {
        "lab_optimization_milestone_payload",
        "lab_unified_replay_append",
        "lab_replay_timeline_payload",
    }
)


def _rel(path: Path) -> str:
    return path.relative_to(_OPTIMIZATION_ROOT).as_posix()


def _py_files() -> list[Path]:
    return sorted(_OPTIMIZATION_ROOT.rglob("*.py"))


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def _import_module_strings(tree: ast.Module) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.append((node.module, node.lineno))
    return out


def _module_segments(module: str) -> list[str]:
    return module.split(".")


def _forbidden_import_reason(rel: str, module: str) -> str | None:
    if module.startswith("django_apps.shapez_asteroid") or module.startswith("shapez_asteroid"):
        return "removed shapez_asteroid namespace"
    if "solver_runtime_pipeline" in module:
        return "monolith solver_runtime_pipeline"
    if "pass_first" in module:
        return "pass_first path"
    if module.startswith("django_apps.asteroid_lab.genetic_sample"):
        return "genetic_sample is non-runtime"
    if module == "django_apps.asteroid_lab.services.lab_rttp_snapshot_compose":
        return "lab_rttp_snapshot_compose belongs on runtime entry only"
    for needle in _SERVICE_ADAPTER_NEEDLES:
        if needle in module:
            return f"replay read adapter {needle!r}"
    if "legacy" in _module_segments(module):
        return "legacy import segment"
    if module.startswith("django_apps.asteroid_lab.replay"):
        if rel not in {"pipeline.py", "rttp_solver_summary.py"}:
            return "replay package import outside allowlist"
        return None
    if module.startswith("django_apps.asteroid_lab.reconstruction"):
        if rel not in {"reconstruction_adapter.py", "rttp_solver_summary.py"}:
            return "reconstruction import outside allowlist"
        return None
    if module.startswith("django_apps.asteroid_lab.services"):
        if rel not in {"reconstruction_adapter.py", "pipeline.py", "replay_sink.py"}:
            return "services import outside allowlist"
        return None
    if module.startswith("django_apps.asteroid_lab.adapters"):
        tail = module.removeprefix("django_apps.asteroid_lab.adapters.")
        if not tail.startswith("catalog_"):
            return "non-catalog adapter import"
        return None
    return None


def test_optimization_imports_respect_forbidden_prefixes_and_allowlist() -> None:
    violations: list[str] = []
    for path in _py_files():
        rel = _rel(path)
        for module, lineno in _import_module_strings(_parse(path)):
            reason = _forbidden_import_reason(rel, module)
            if reason:
                violations.append(f"{rel}:{lineno}: {module!r} — {reason}")
    assert violations == []
```

- [ ] **Step 2: Run import gate test on current tree**

```powershell
python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py::test_optimization_imports_respect_forbidden_prefixes_and_allowlist -v --tb=short
```

Expected: **PASS** (no production edits required on current tree)

- [ ] **Step 3: Commit**

```bash
git add tests/unit/architecture/test_optimization_contamination_gates.py
git commit -m "test(architecture): add PR-B optimization import contamination gate"
```

---

## Task 2: Closed allowlist set test

**Files:**

- Modify: `tests/unit/architecture/test_optimization_contamination_gates.py`

- [ ] **Step 1: Add closed-set test**

Append to the same test file:

```python
def _imports_external_boundary_modules(tree: ast.Module) -> bool:
    prefixes = (
        "django_apps.asteroid_lab.reconstruction",
        "django_apps.asteroid_lab.services",
        "django_apps.asteroid_lab.replay",
        "django_apps.asteroid_lab.adapters",
    )
    for module, _lineno in _import_module_strings(tree):
        if any(module.startswith(p) for p in prefixes):
            return True
    return False


def test_optimization_allowlist_files_are_closed_set() -> None:
    """Any file importing reconstruction/services/replay/adapters must be allowlisted."""
    offenders: list[str] = []
    for path in _py_files():
        rel = _rel(path)
        if _imports_external_boundary_modules(_parse(path)) and rel not in _ALLOWLIST_EXTRA:
            offenders.append(rel)
    assert offenders == [], (
        "Add file to _ALLOWLIST_EXTRA in spec §2.4 or remove forbidden import: "
        + ", ".join(offenders)
    )
```

- [ ] **Step 2: Run closed-set test**

```powershell
python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py::test_optimization_allowlist_files_are_closed_set -v --tb=short
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/unit/architecture/test_optimization_contamination_gates.py
git commit -m "test(architecture): enforce PR-B optimization allowlist closed set"
```

---

## Task 3: AST decision-path token gate

**Files:**

- Modify: `tests/unit/architecture/test_optimization_contamination_gates.py`

- [ ] **Step 1: Add token-scan helpers and test**

Append:

```python
def _decision_paths() -> list[Path]:
    paths: list[Path] = []
    for path in _py_files():
        rel = _rel(path)
        if rel in _TOKEN_EXCLUDE_FILES:
            continue
        first = rel.split("/", 1)[0]
        if first in _DECISION_SUBDIRS:
            paths.append(path)
    return paths


def _docstring_node_ids(tree: ast.Module) -> set[int]:
    doc = ast.get_docstring(tree, clean=False)
    if not doc:
        return set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if ast.get_docstring(node, clean=False) == doc:
                return {id(n) for n in ast.walk(node)}
    return set()


def _forbidden_tokens_in_tree(tree: ast.Module) -> list[str]:
    doc_ids = _docstring_node_ids(tree)
    hits: list[str] = []

    def check_id(name: str, lineno: int) -> None:
        if name in _FORBIDDEN_TOKEN_IDS:
            hits.append(f"L{lineno}: identifier {name!r}")

    for node in ast.walk(tree):
        if id(node) in doc_ids:
            continue
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in _FORBIDDEN_TOKEN_IDS:
                    check_id(alias.name, node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module in _FORBIDDEN_TOKEN_IDS:
                check_id(node.module, node.lineno)
            for alias in node.names:
                if alias.name in _FORBIDDEN_TOKEN_IDS:
                    check_id(alias.name, node.lineno)
        elif isinstance(node, ast.Name):
            check_id(node.id, node.lineno)
        elif isinstance(node, ast.Attribute):
            check_id(node.attr, node.lineno)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            for token in _FORBIDDEN_TOKEN_IDS:
                if token in node.value:
                    hits.append(f"L{node.lineno}: string literal contains {token!r}")
    return hits


def test_optimization_decision_paths_forbid_algorithm_input_tokens() -> None:
    violations: list[str] = []
    for path in _decision_paths():
        rel = _rel(path)
        hits = _forbidden_tokens_in_tree(_parse(path))
        if hits:
            violations.append(f"{rel}: " + "; ".join(hits))
    assert violations == []
```

- [ ] **Step 2: Run token gate**

```powershell
python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py::test_optimization_decision_paths_forbid_algorithm_input_tokens -v --tb=short
```

Expected: PASS

- [ ] **Step 3: Run full PR-B test module**

```powershell
python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py -v --tb=short
```

Expected: 3 passed

- [ ] **Step 4: Commit**

```bash
git add tests/unit/architecture/test_optimization_contamination_gates.py
git commit -m "test(architecture): add PR-B AST decision-path token gate"
```

---

## Task 4: Absorb legacy milestone test

**Files:**

- Delete: `tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py`

- [ ] **Step 1: Confirm milestone needles covered**

Grep shows needles only appeared as substring test; PR-B covers them via `_SERVICE_ADAPTER_NEEDLES` on import module strings.

```powershell
rg "lab_optimization_milestone_payload|lab_unified_replay_append|lab_replay_timeline_payload" django_apps/asteroid_lab/optimization
```

Expected: no matches (or only comments — if comment-only, OK)

- [ ] **Step 2: Delete legacy test file**

```bash
git rm tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py
```

- [ ] **Step 3: Run PR-B + catalog architecture gates**

```powershell
python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v --tb=short
```

Expected: all pass

- [ ] **Step 4: Commit**

```bash
git commit -m "test(asteroid-lab): remove milestone import boundary absorbed by PR-B"
```

---

## Task 5: Standing gate script (optional) + ruff

**Files:**

- Create: `scripts/test_optimization_contamination.ps1` (optional)

- [ ] **Step 1: Add PowerShell wrapper**

Create `scripts/test_optimization_contamination.ps1`:

```powershell
# PR-B standing gate — optimization import canon (see current_plan.md).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v --tb=short @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m ruff check django_apps/asteroid_lab/optimization
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

- [ ] **Step 2: Run wrapper**

```powershell
powershell -File scripts/test_optimization_contamination.ps1
```

Expected: exit 0

- [ ] **Step 3: Commit**

```bash
git add scripts/test_optimization_contamination.ps1
git commit -m "chore(scripts): add PR-B optimization contamination standing gate"
```

---

## Task 6: Documentation — `current_plan.md` + roadmap

**Files:**

- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`

- [ ] **Step 1: Update `current_plan.md`**

In **Next focus**, replace PR-B implicit queue with:

```markdown
**Priority:** PR-B Decontamination optimization contamination gates (ACTIVE after Entry Gate A).
Standing: reconstruction narrow + RTTP narrow + PR-B architecture gate.
```

Add under **Maintenance / Standing Gates**:

```markdown
- **PR-B optimization contamination gate owner:** `powershell -File scripts/test_optimization_contamination.ps1`
  - Or: `python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v --tb=short`
```

Add **Closed** section entry when PR merges (placeholder during implementation):

```markdown
- Decontamination PR-B — Optimization contamination gates
  - Status: CLOSED
  - Spec: docs/superpowers/specs/2026-05-24-decontamination-pr-b-optimization-gates-design.md
  - Evidence: test_optimization_contamination_gates.py green; milestone test removed
```

- [ ] **Step 2: Update roadmap**

In `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` **Progress at a glance** table:

| Axis | Open next |
|------|-----------|
| **Repo** | PR-B optimization contamination gate → PR-D/E |

Add short **PR-B** subsection under maintenance or new **Decontamination** heading with link to spec.

- [ ] **Step 3: Commit**

```bash
git add documents/ai/current_plan.md docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md
git commit -m "docs: queue PR-B optimization contamination gates"
```

---

## Task 7: PR-B closure verification

**Files:** none

- [ ] **Step 1: Re-run Entry Gate A blocking gates**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
powershell -File scripts/test_optimization_contamination.ps1
```

Expected: all exit 0

- [ ] **Step 2: Mark PR-B CLOSED in docs with merge SHA**

Update `current_plan.md` Closed entry with actual merge commit SHA.

- [ ] **Step 3: Optional full gate before PR**

```powershell
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m black --check .
python -m mypy django_apps config src
```

Expected: pass (user/CI policy)

---

## Plan self-review (spec coverage)

| Spec section | Task |
|--------------|------|
| §1 Entry Gate A | Task 0 |
| §2.1 Scanned root | Task 1 `_py_files` |
| §2.2 Forbidden imports | Task 1 `_forbidden_import_reason` |
| §2.3B Service needles | Task 1 `_SERVICE_ADAPTER_NEEDLES` |
| §2.3C AST tokens | Task 3 |
| §2.4 Closed allowlist | Task 2 |
| §2.5 Absorb/delete | Task 4 |
| §2.6 Standing gate | Task 5–6 |
| §2.8 Closure | Task 7 |

No TBD placeholders. Production code change not required on current tree.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-24-decontamination-pr-b-optimization-gates.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — run tasks in this session with executing-plans checkpoints  

**Which approach?**

**Design spec:** `docs/superpowers/specs/2026-05-24-decontamination-pr-b-optimization-gates-design.md` — please review before implementation if you want spec edits; plan assumes approved text.
