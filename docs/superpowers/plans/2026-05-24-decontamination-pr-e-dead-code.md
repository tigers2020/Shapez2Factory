# Decontamination PR-E — Dead Code Deletion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Physically delete PR-D–declared dead test artifacts (2 files + 1 pytest node), leave quarantine registry in applied-only final state, and prove gates stay green with no runtime change.

**Architecture:** Promote deletions into `PrEDeleteCandidate` records with `replacements: tuple[str, ...]`; move all rows to `PR_E_APPLIED_DELETIONS` with `PR_E_DELETE_CANDIDATES = ()`; replace PR-D pending-disposition test with applied-only architecture tests that verify absence + replacement presence.

**Tech Stack:** Python 3.12+, dataclasses, ast, pytest, ruff, PowerShell standing scripts.

**Spec:** [`../specs/2026-05-24-decontamination-pr-e-dead-code-design.md`](../specs/2026-05-24-decontamination-pr-e-dead-code-design.md)

**Branch:** `feat/decontamination-pr-e-dead-code` from current `master` (worktree recommended).

---

## File map

| File | Action |
|------|--------|
| `tests/unit/architecture/quarantine_registry.py` | Modify — `PrEDeleteCandidate`, applied-only tuples |
| `tests/unit/architecture/test_quarantined_paths_do_not_leak.py` | Modify — replace PR-D PR-E disposition test with applied-only suite |
| `tests/unit/asteroid_lab/test_service_import_boundaries.py` | Delete (E-1) |
| `tests/test_smoke.py` | Delete (E-2) |
| `tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py` | Modify — remove E-3 function only |
| `docs/superpowers/reports/2026-05-24-test-cleanup-audit.md` | Create — move/rewrite from `docs/ai/test_cleanup_audit.md` |
| `docs/ai/test_cleanup_audit.md` | Delete after move (or leave stub redirect — prefer delete to avoid duplicate authority) |
| `documents/ai/current_plan.md` | Modify — PR-E ACTIVE → CLOSED |
| `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | Modify — PR-E row |
| `docs/superpowers/specs/2026-05-24-decontamination-pr-e-dead-code-design.md` | Modify — Status CLOSED after merge |

**Do not modify:** `django_apps/**` production code, `QUARANTINED_DOC_PATHS` trees, PR-B gate logic.

---

### Task 0: Baseline verification and collection count

**Files:**
- Read-only: repo root

- [ ] **Step 1: Sync `master` and create branch**

```powershell
git checkout master
git pull
git checkout -b feat/decontamination-pr-e-dead-code
```

- [ ] **Step 2: Record baseline gates (must be green before edits)**

```powershell
powershell -File scripts/test_quarantine_registry.ps1
powershell -File scripts/test_optimization_contamination.ps1
```

Expected: quarantine 5 passed; optimization contamination passed.

- [ ] **Step 3: Record collection count BEFORE deletions**

```powershell
python -m pytest --collect-only tests 2>&1 | Tee-Object -FilePath var/log/pr_e_collect_before.txt
```

Parse the final line `N tests collected` (or equivalent summary). **Write this number into your PR notes** — expected AFTER delta is **N − 2**.

Expected collection delta (document in PR body):

```text
- E-1 0-byte file removed: no collected test delta
- E-2 tests/test_smoke.py removed: -1 test
- E-3 replay pytest node removed: -1 test
Total expected test item delta: -2
```

- [ ] **Step 4: Confirm deletion targets exist pre-change**

```powershell
python -c "from pathlib import Path; p=Path('tests/unit/asteroid_lab/test_service_import_boundaries.py'); print(p.stat().st_size, p.is_file())"
python -c "import ast; from pathlib import Path; t=Path('tests/test_smoke.py').read_text(); print('assert True' in t)"
python -c "import ast; from pathlib import Path; m=ast.parse(Path('tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py').read_text()); print([n.name for n in m.body if isinstance(n, ast.FunctionDef)])"
```

Expected: size `0`; smoke contains `assert True`; replay file lists both `test_unified_replay_event_type_adapter_coverage_matrix_is_explicit` and `test_lab_adapter_members_are_valid_replay_event_types`.

---

### Task 1: Registry schema — `PrEDeleteCandidate` and applied-only tuples

**Files:**
- Modify: `tests/unit/architecture/quarantine_registry.py`
- Test: `tests/unit/architecture/test_quarantined_paths_do_not_leak.py` (imports only — full test update in Task 4)

- [ ] **Step 1: Replace PR-D `tuple[str]` with typed records**

In `quarantine_registry.py`, add imports and dataclass; replace tail of file from `PR_E_DELETE_CANDIDATES` onward:

```python
from typing import Literal

PrEKind = Literal["file", "pytest_node"]


@dataclass(frozen=True, slots=True)
class PrEDeleteCandidate:
    path: str
    kind: PrEKind
    reason: str
    evidence: str
    replacements: tuple[str, ...]


PR_E_DELETE_CANDIDATES: tuple[PrEDeleteCandidate, ...] = ()

PR_E_APPLIED_DELETIONS: tuple[PrEDeleteCandidate, ...] = (
    PrEDeleteCandidate(
        path="tests/unit/asteroid_lab/test_service_import_boundaries.py",
        kind="file",
        reason="zero_byte_test_file",
        evidence="0-byte file; collects zero tests",
        replacements=(
            "tests/unit/architecture/test_django_app_import_boundaries.py",
            "tests/unit/architecture/test_optimization_contamination_gates.py",
        ),
    ),
    PrEDeleteCandidate(
        path="tests/test_smoke.py",
        kind="file",
        reason="meaningless_placeholder",
        evidence=(
            "sole test is assert True; CI and pytest collection already cover test discovery"
        ),
        replacements=("tests/integration/api/test_health.py",),
    ),
    PrEDeleteCandidate(
        path=(
            "tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py"
            "::test_lab_adapter_members_are_valid_replay_event_types"
        ),
        kind="pytest_node",
        reason="duplicate_coverage",
        evidence=(
            "loops SUPPORTED_BY_9B_LAB_ADAPTER with member in ReplayEventType only"
        ),
        replacements=(
            "tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py"
            "::test_unified_replay_event_type_adapter_coverage_matrix_is_explicit",
        ),
    ),
)
```

Keep `QUARANTINED_MODULE_PREFIXES`, `QUARANTINED_DOC_PATHS`, `ACTIVE_RUNTIME_ROOTS`, `MAX_TRANSITIVE_IMPORT_DEPTH` unchanged.

- [ ] **Step 2: Fix spec reference line at top of registry module**

```python
"""PR-D/PR-E quarantine registry — machine-readable stale path isolation.

Spec: docs/superpowers/specs/2026-05-24-decontamination-pr-d-quarantine-design.md
PR-E: docs/superpowers/specs/2026-05-24-decontamination-pr-e-dead-code-design.md
"""
```

- [ ] **Step 3: Run ruff on registry (expect PR-D test import breakage until Task 4)**

```powershell
python -m ruff check tests/unit/architecture/quarantine_registry.py
```

Expected: ruff PASS on registry file alone.

**Note:** Do **not** commit deletions yet. Registry reflects **final** applied-only state per spec even before files are removed; Task 4 tests will fail until Task 3.

---

### Task 2: Physical deletions (E-1, E-2, E-3)

**Files:**
- Delete: `tests/unit/asteroid_lab/test_service_import_boundaries.py`
- Delete: `tests/test_smoke.py`
- Modify: `tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py`

- [ ] **Step 1: Delete E-1 and E-2 files**

```powershell
git rm tests/unit/asteroid_lab/test_service_import_boundaries.py
git rm tests/test_smoke.py
```

- [ ] **Step 2: Remove E-3 pytest function only**

Delete the entire function block from `test_replay_event_coverage_matrix.py` (keep imports and `test_unified_replay_event_type_adapter_coverage_matrix_is_explicit`):

```python
# REMOVE this function entirely — do not leave a stub.

def test_lab_adapter_members_are_valid_replay_event_types() -> None:
    for member in SUPPORTED_BY_9B_LAB_ADAPTER:
        assert member in ReplayEventType
```

After edit, file ends with only `test_unified_replay_event_type_adapter_coverage_matrix_is_explicit`.

- [ ] **Step 3: Verify targets absent**

```powershell
python -c "from pathlib import Path; assert not Path('tests/unit/asteroid_lab/test_service_import_boundaries.py').exists()"
python -c "from pathlib import Path; assert not Path('tests/test_smoke.py').exists()"
python -c "import ast; from pathlib import Path; names=[n.name for n in ast.parse(Path('tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py').read_text()).body if isinstance(n, ast.FunctionDef)]; assert 'test_lab_adapter_members_are_valid_replay_event_types' not in names"
```

Expected: all assertions pass.

- [ ] **Step 4: Run replay matrix tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py -v --tb=short
```

Expected: 1 passed (only explicit matrix test remains).

---

### Task 3: Applied-only architecture tests

**Files:**
- Modify: `tests/unit/architecture/test_quarantined_paths_do_not_leak.py`

- [ ] **Step 1: Update imports**

```python
from tests.unit.architecture.quarantine_registry import (
    _INTERNAL_IMPORT_PREFIX,
    ACTIVE_RUNTIME_ROOTS,
    MAX_TRANSITIVE_IMPORT_DEPTH,
    PR_E_APPLIED_DELETIONS,
    PR_E_DELETE_CANDIDATES,
    PrEDeleteCandidate,
    QUARANTINED_DOC_PATHS,
    QUARANTINED_MODULE_PREFIXES,
)
```

Update module docstring spec link to include PR-E design path.

- [ ] **Step 2: Add helpers after `_matches_quarantined_prefix`**

```python
def _split_pytest_nodeid(nodeid: str) -> tuple[str, str]:
    if "::" not in nodeid:
        raise ValueError(f"expected pytest nodeid, got: {nodeid!r}")
    file_part, func_part = nodeid.split("::", 1)
    return file_part, func_part


def _function_defined_in_module(module_rel: str, func_name: str) -> bool:
    path = _repo_path(module_rel)
    assert path.is_file(), f"missing module for node check: {module_rel}"
    tree = _parse(path)
    return any(
        isinstance(node, ast.FunctionDef) and node.name == func_name for node in tree.body
    )


def _replacement_exists(replacement: str) -> bool:
    if "::" in replacement:
        module_rel, func_name = _split_pytest_nodeid(replacement)
        return _function_defined_in_module(module_rel, func_name)
    return _repo_path(replacement).is_file()
```

- [ ] **Step 3: Remove `test_quarantine_registry_has_pr_e_disposition`**

Delete the entire function (PR-D pending-candidate test).

- [ ] **Step 4: Add applied-only tests**

```python
def test_pr_e_delete_candidates_empty() -> None:
    assert PR_E_DELETE_CANDIDATES == ()


def test_pr_e_applied_deletions_recorded() -> None:
    assert len(PR_E_APPLIED_DELETIONS) == 3
    paths = [entry.path for entry in PR_E_APPLIED_DELETIONS]
    assert len(paths) == len(set(paths))
    for entry in PR_E_APPLIED_DELETIONS:
        assert entry.kind in ("file", "pytest_node")
        assert entry.reason.strip()
        assert entry.evidence.strip()
        assert isinstance(entry.replacements, tuple)


def test_pr_e_applied_files_absent() -> None:
    missing: list[str] = []
    for entry in PR_E_APPLIED_DELETIONS:
        if entry.kind != "file":
            continue
        if _repo_path(entry.path).is_file():
            missing.append(entry.path)
    assert missing == [], f"deleted files still on disk: {missing}"


def test_pr_e_applied_pytest_nodes_absent() -> None:
    missing: list[str] = []
    for entry in PR_E_APPLIED_DELETIONS:
        if entry.kind != "pytest_node":
            continue
        module_rel, func_name = _split_pytest_nodeid(entry.path)
        if _function_defined_in_module(module_rel, func_name):
            missing.append(entry.path)
    assert missing == [], f"deleted pytest nodes still defined: {missing}"


def test_pr_e_replacement_targets_exist() -> None:
    missing: list[str] = []
    for entry in PR_E_APPLIED_DELETIONS:
        for replacement in entry.replacements:
            if not _replacement_exists(replacement):
                missing.append(f"{entry.path} -> {replacement}")
    assert missing == [], f"missing replacements: {missing}"
```

- [ ] **Step 5: Run quarantine gate**

```powershell
powershell -File scripts/test_quarantine_registry.ps1
```

Expected: **9 passed** (4 retained PR-D tests + 5 new PR-E tests; removed `test_quarantine_registry_has_pr_e_disposition`).

- [ ] **Step 6: Commit deletion + registry + tests (single logical commit or two)**

```bash
git add tests/unit/architecture/quarantine_registry.py tests/unit/architecture/test_quarantined_paths_do_not_leak.py tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py
git add -u tests/unit/asteroid_lab/test_service_import_boundaries.py tests/test_smoke.py
git commit -m "test(arch): PR-E dead code deletion and applied registry state"
```

---

### Task 4: Evidence report (non-authority)

**Files:**
- Create: `docs/superpowers/reports/2026-05-24-test-cleanup-audit.md`
- Delete: `docs/ai/test_cleanup_audit.md` (if present)

- [ ] **Step 1: Create report with disclaimer header**

Top of file:

```markdown
# Test Cleanup Audit (Evidence Report)

**Date:** 2026-05-24  
**Authority:** None — evidence only. Deletions are authorized only by `PR_E_APPLIED_DELETIONS` in `quarantine_registry.py`.

**PR-E applied (2026-05-24):**

| id | path | disposition |
|----|------|-------------|
| E-1 | `tests/unit/asteroid_lab/test_service_import_boundaries.py` | deleted |
| E-2 | `tests/test_smoke.py` | deleted |
| E-3 | `...::test_lab_adapter_members_are_valid_replay_event_types` | function removed |
```

- [ ] **Step 2: Copy inventory table from draft `docs/ai/test_cleanup_audit.md`**

Fix stale replacement row for E-1: remove reference to `test_optimization_milestone_import_boundary.py` (removed in PR-B). Point import boundaries to `test_django_app_import_boundaries.py` and `test_optimization_contamination_gates.py`.

- [ ] **Step 3: Add PR-E verification section with actual collect counts**

```markdown
## PR-E verification

- collect-before: <N> (from Task 0)
- collect-after: <M> (from Task 5)
- delta: <M - N> (expected -2)
```

- [ ] **Step 4: Remove draft path**

```powershell
git rm docs/ai/test_cleanup_audit.md
```

If file was never tracked, `git add docs/superpowers/reports/2026-05-24-test-cleanup-audit.md` only.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/reports/2026-05-24-test-cleanup-audit.md
git commit -m "docs: add PR-E test cleanup evidence report"
```

---

### Task 5: Blocking verification and collection delta

**Files:**
- Append: `docs/superpowers/reports/2026-05-24-test-cleanup-audit.md` (counts)

- [ ] **Step 1: Run blocking commands**

```powershell
powershell -File scripts/test_quarantine_registry.ps1
powershell -File scripts/test_optimization_contamination.ps1
python -m pytest tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py -v --tb=short
python -m pytest --collect-only tests 2>&1 | Tee-Object -FilePath var/log/pr_e_collect_after.txt
```

Expected: all green; collect-after = collect-before − 2.

- [ ] **Step 2: Run recommended commands**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
```

- [ ] **Step 3: Record delta in evidence report and PR notes**

```text
Expected collection delta: -2
Actual: <before> -> <after> = <delta>
```

- [ ] **Step 4: Lint touched Python**

```powershell
python -m ruff check tests/unit/architecture/quarantine_registry.py tests/unit/architecture/test_quarantined_paths_do_not_leak.py tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py
```

Expected: PASS.

---

### Task 6: Documentation and controller closure

**Files:**
- Modify: `documents/ai/current_plan.md`
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`
- Modify: `docs/superpowers/specs/2026-05-24-decontamination-pr-e-dead-code-design.md`

- [ ] **Step 1: Add PR-E CLOSED block to `current_plan.md`**

Mirror PR-D format:

```markdown
- Decontamination PR-E — Dead code deletion
  - Status: **CLOSED** (master)  # or branch-local until merge
  - Spec: docs/superpowers/specs/2026-05-24-decontamination-pr-e-dead-code-design.md
  - Plan: docs/superpowers/plans/2026-05-24-decontamination-pr-e-dead-code.md
  - Evidence: PR_E_DELETE_CANDIDATES empty; PR_E_APPLIED_DELETIONS (3); collect delta -2; quarantine + optimization gates green
```

Update **Next focus** to deferred commit retry (post PR-E).

- [ ] **Step 2: Roadmap decontamination section**

Under PR-D row, add PR-E CLOSED with merge SHA when available; change “Open next” from PR-E to deferred commit retry.

- [ ] **Step 3: Set spec status**

In `2026-05-24-decontamination-pr-e-dead-code-design.md`:

```markdown
**Status:** CLOSED (merged to `master` <sha>, PR #<n>, 2026-05-24)
```

Add implementation plan link in header.

- [ ] **Step 4: Self-review checklist (agent)**

- [ ] `PR_E_DELETE_CANDIDATES == ()` on branch tip
- [ ] Three applied records with correct `replacements` tuples
- [ ] No `django_apps/**` diff
- [ ] Evidence report states non-authority
- [ ] Collection delta documented as −2

---

## Plan self-review (spec coverage)

| Spec § | Task |
|--------|------|
| §1 principles | Tasks 1–6; evidence report disclaimer Task 4 |
| §2 schema `replacements` tuple | Task 1 |
| §3 E-1/E-2/E-3 | Task 2 |
| §4 applied-only tests | Task 3 |
| §5 evidence report | Task 4 |
| §6 verification | Task 0, 5 |
| §7 docs | Task 6 |
| §8 closure | Task 5–6 |
| §9 out of scope | File map exclusions |
| §10–11 risks/rollback | Acknowledged in spec; no extra tasks |

**Placeholder scan:** None.

---

## Full gate (pre-PR merge)

Per `AGENTS.md` when opening PR:

```powershell
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m mypy django_apps config src
python -m black --check .
```

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-24-decontamination-pr-e-dead-code.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session with executing-plans checkpoints  

**Which approach?**
