# Asteroid Lab — Reconstruction Complete-Map Decontamination — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Status:** **CLOSED (2026-05-27, branch-local)** — PR-B complete on `feat/decontamination-recon-complete-map-pr-b`; merge PR pending  
> **Spec:** [`2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md`](../specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md)  
> **Forbidden during this plan:** MEG-C2, RTTP feature work, v0.2 core algorithm recovery implementation  
> **Branch:** `feat/decontamination-recon-complete-map` (dedicated worktree recommended)

**Goal:** Hard-delete Asteroid Lab RTTP/optimization runtime and docs; keep reconstruction through `ReconstructionCompleteMap` product slice only; `run_solver` → `SOLVER_NOT_AVAILABLE`.

**Architecture:** Extraction-verify → PR-A stub + import-zero reconstruction → PR-B delete packages/services/tests/docs → invert contamination gates. Two PRs to `master`; no MEG wiring.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy `django_apps config src`, PowerShell gate scripts

---

## File map (summary)

| Action | Path |
|--------|------|
| Keep | `django_apps/asteroid_lab/reconstruction/**`, `cleanup/**`, `replay/` (recon), `contracts/game_data_snapshot*.py`, `genetic_sample/**`, `reconstruction_capacity_summary.py` |
| Stub | `django_apps/asteroid_lab/services/solver_runtime_entry.py` |
| Delete PR-B | `django_apps/asteroid_lab/optimization/`, `catalog/`, RTTP `contracts/catalog_*`, RTTP `adapters/catalog_*`, RTTP services (see Task 4) |
| Delete PR-B | `tests/**/*rttp*`, `tests/**/*optimization*` (per registry), `harness/investigation/rttp_*` |
| Docs PR-B | Hard-delete active RTTP specs/plans; archive ≤10 closed plans; archive README |

---

## Task 0: Governance guard

**Files:**
- Modify: `docs/superpowers/specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md` (header — done if plan author sees SUSPENDED line)
- Modify: `docs/superpowers/plans/2026-05-27-rttp-mining-equipment-goal.md`
- Modify: `documents/ai/current_plan.md`

- [x] **Step 1: MEG implementation plan — block execution**

Add immediately after the plan title in `docs/superpowers/plans/2026-05-27-rttp-mining-equipment-goal.md`:

```markdown
> **DO NOT EXECUTE** — SUSPENDED by [decontamination design](../specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md). Historical reference only. MEG-C2 forbidden until RTTP explicitly re-opened.
```

- [x] **Step 2: Strike legacy ACTIVE RTTP rows in `current_plan.md`**

For each line matching `**ACTIVE` that references RTTP / ELCP / v0.2 recovery / MEG (approx. lines 114–160+), prefix:

```markdown
**BLOCKED (decontamination P0):**
```

and add one line under the P0 banner:

```markdown
- Legacy ACTIVE rows below are **historical only** — do not implement until decontamination CLOSED.
```

Do **not** delete historical CLOSED/REOPENED forensic rows (audit trail).

- [x] **Step 3: Link implementation plan in decontamination spec §15**

In `docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md` §15, set:

```markdown
**Implementation plan:** [`2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md`](../plans/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md)
```

- [ ] **Step 4: Commit (docs-only)** — **withheld** until user requests commit

```bash
git add docs/superpowers/plans/2026-05-27-rttp-mining-equipment-goal.md documents/ai/current_plan.md docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md docs/superpowers/plans/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md
git commit -m "docs: block MEG plan and align current_plan with P0 decontamination"
```

---

## Task 1: Extraction inventory (verify before delete)

**No code delete in this task** — inventory only; fix gaps before PR-A.

> **Inventory completed 2026-05-27 (Task 0.5 follow-up):** GATE-R6 green; `grid_contract` + `game_data_snapshot` in `contracts/` present; `genetic_sample/` clean; 10 `catalog/` + 11 `adapters/catalog_*` + 8 RTTP `services/` + `solver_runtime_entry` import `optimization` — PR-B delete list below.

- [x] **Step 1: GATE-R6 baseline (reconstruction must already be clean)**

```powershell
cd f:\Python_Projects\shapez2Factory
rg "django_apps\.asteroid_lab\.(optimization|catalog)" django_apps/asteroid_lab/reconstruction
```

Expected: **no matches**. If matches exist, rewire to `snapshots/grid_contract.py` or `reconstruction/acceptance_topology.py` before PR-A.

- [x] **Step 2: `grid_contract` parity**

Confirm `django_apps/asteroid_lab/snapshots/grid_contract.py` exports: `Coord`, `BBox`, `bbox_from_coords`, `expand_bbox`, `cells_in_bbox` (and `neighbors4` if any recon consumer needs it).

Grep consumers still on `optimization.coords`:

```powershell
rg "optimization\.coords|optimization\.input_contracts" django_apps/asteroid_lab --glob "!optimization/**" --glob "!catalog/**"
```

Expected after PR-B: **0** (PR-A may leave services that PR-B deletes).

- [x] **Step 3: `acceptance_topology` parity**

Read `django_apps/asteroid_lab/reconstruction/acceptance_topology.py` — must satisfy `confidence.py` without `optimization_input_from_reconstruction`.

- [x] **Step 4: `game_data_snapshot`**

Confirm `django_apps/asteroid_lab/contracts/game_data_snapshot.py` exists; web adapter imports `contracts` not `optimization`:

```powershell
rg "optimization\.game_data" django_apps
```

Expected: **0**.

- [x] **Step 5: `genetic_sample` scan**

```powershell
rg "optimization" django_apps/asteroid_lab/genetic_sample django_apps/asteroid_lab/genetic_sample_mini_map.py django_apps/asteroid_lab/admin.py
```

If `optimization/gene_template` still imported, move to `genetic_sample/` (strip-solver Task 4) **before** PR-B.

- [x] **Step 6: Record inventory in PR description**

List non-`optimization/` modules that import `optimization` (from Step 2 rg) — these are PR-B delete or trim targets:

| Module (examples) | PR-B action |
|-------------------|-------------|
| `services/solver_runtime_entry.py` | Stub in PR-A |
| `services/lab_rttp_snapshot_compose.py` | Delete |
| `services/placement_goal.py` | Delete |
| `services/mining_equipment_goal.py` | Delete |
| `services/lab_replay_timeline_payload.py` | Trim RTTP branches |
| `adapters/catalog_*` | Delete |
| `contracts/catalog_*`, `exterior_lane_*` | Delete |

---

## Task 2: PR-A — Stub and rewrite entrypoints

**PR title:** `feat(asteroid_lab): decontamination PR-A — solver stub, zero RTTP branch`

### Task 2a: `solver_runtime_entry` always stub

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Modify: `config/settings/base.py` (or RTTP flag definition site) — remove or deprecate `ASTEROID_LAB_RTTP_ENABLED`

- [ ] **Step 1: Write failing test — stub always**

Create `tests/unit/asteroid_lab/test_solver_decontamination_stub.py`:

```python
"""Post-decontamination: run_solver entry is always SOLVER_NOT_AVAILABLE."""

from __future__ import annotations

import pytest
from django.test import override_settings

from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SolverRuntimeEntryErrorCode,
    run_solver_for_map_input,
)


@pytest.mark.django_db
@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)  # flag must not resurrect RTTP
def test_run_solver_always_not_available(map_input_factory):
    inp = map_input_factory()
    result = run_solver_for_map_input(inp.pk)
    assert result.error_code == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE
    assert result.ok is False
```

Adjust `map_input_factory` to match project fixture name (`asteroid_map_input` or existing pattern in `tests/unit/asteroid_lab/conftest.py`).

- [ ] **Step 2: Run test — expect FAIL** (RTTP still runs when flag True)

```bash
python -m pytest tests/unit/asteroid_lab/test_solver_decontamination_stub.py -v --tb=short
```

- [ ] **Step 3: Implement stub-only entry**

In `solver_runtime_entry.py`:

- Remove `from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline` (and all optimization imports).
- Delete `_rttp_enabled()` branch; public entry always returns:

```python
return SolverRuntimeEntryResult(
    ok=False,
    error_code=SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE,
    message=SOLVER_NOT_AVAILABLE_MESSAGE,
)
```

- Keep reconstruction helpers if used by Lab reconstruct path; remove RTTP replay sink wiring.

- [ ] **Step 4: Remove or ignore `ASTEROID_LAB_RTTP_ENABLED`**

In settings: delete setting **or** document in comment "ignored post-decontamination". No code path may call `run_rttp_pipeline`.

- [ ] **Step 5: Re-run stub test — PASS**

```bash
python -m pytest tests/unit/asteroid_lab/test_solver_decontamination_stub.py -v --tb=short
```

### Task 2b: HTTP view fail-closed

**Files:**
- Modify: `django_apps/web/views/public_pages.py` (run_solver handler)
- Test: `tests/integration/web/test_asteroid_run_solver.py`

- [ ] **Step 1: Update integration test — both flag values return stub**

Add or change test so `@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)` still gets `ok: false`, `error_code == SOLVER_NOT_AVAILABLE`, HTTP 200.

- [ ] **Step 2: Run integration test**

```bash
python -m pytest tests/integration/web/test_asteroid_run_solver.py -v --tb=short
```

- [ ] **Step 3: View try/except** — any exception from entry still returns same JSON body (GATE-R5).

### Task 2c: `manage.py run_solver`

**Files:**
- Modify or delete: `django_apps/asteroid_lab/management/commands/run_solver.py`

- [ ] **Step 1:** Command prints `SOLVER_NOT_AVAILABLE` and exits non-zero without importing `optimization`.

```bash
python manage.py run_solver --slug test 2>&1 | findstr SOLVER_NOT_AVAILABLE
```

- [ ] **Step 2: Delete or rewrite `test_run_solver_management_command.py` RTTP tests** — keep only stub expectation; remove `@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)` pipeline tests in PR-A or PR-B.

### Task 2d: PR-A commit

```bash
python -m ruff check django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/web/views/public_pages.py
git add django_apps/asteroid_lab/services/solver_runtime_entry.py config/ tests/unit/asteroid_lab/test_solver_decontamination_stub.py tests/integration/web/test_asteroid_run_solver.py
git commit -m "feat(asteroid_lab): PR-A solver stub always SOLVER_NOT_AVAILABLE"
```

Open PR-A; CI narrow gates (Task 3) must pass before merge.

---

## Task 3: PR-A gates (verification)

- [ ] **Step 1: Reconstruction narrow**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

Expected: PASS (seven modules + B-CS4).

- [ ] **Step 2: Capacity SoT**

```powershell
powershell -File scripts/test_capacity_sot.ps1
```

Expected: PASS.

- [ ] **Step 3: Complete map unit**

```bash
python -m pytest tests/unit/asteroid_lab/test_complete_map.py tests/unit/asteroid_lab/test_field_cells.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py -v --tb=short
```

- [ ] **Step 4: GATE-R6**

```powershell
rg "django_apps\.asteroid_lab\.optimization" django_apps/asteroid_lab/reconstruction
```

Expected: **0 lines**.

- [ ] **Step 5: Stub tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_solver_decontamination_stub.py tests/integration/web/test_asteroid_run_solver.py -v --tb=short
```

**Note:** Full `pytest -k rttp` will still pass until PR-B deletes tests — do not use as merge gate for PR-A.

---

## Task 4: PR-B — Hard delete code

**PR title:** `feat(asteroid_lab): decontamination PR-B — remove RTTP runtime`

**Precondition:** PR-A merged; `solver_runtime_entry` stub-only.

### Task 4a: Delete packages

- [x] **Step 1: Delete directories**

```text
django_apps/asteroid_lab/optimization/
django_apps/asteroid_lab/catalog/
```

- [x] **Step 2: Delete RTTP contracts** (examples — verify with rg before rm)

```text
django_apps/asteroid_lab/contracts/catalog_candidate.py
django_apps/asteroid_lab/contracts/catalog_placement.py
django_apps/asteroid_lab/contracts/exterior_lane_capacity.py
django_apps/asteroid_lab/contracts/deferred_retry_execute.py
django_apps/asteroid_lab/contracts/ga_evolution_shadow.py
```

Keep: `contracts/game_data_snapshot.py`, `game_data_snapshot_provenance.py`.

- [x] **Step 3: Delete RTTP adapters**

```text
django_apps/asteroid_lab/adapters/catalog_*.py
```

Keep: `adapters/game_data_snapshot_adapter.py`.

### Task 4b: Delete RTTP services

Delete (confirm no reconstruction-only imports):

```text
django_apps/asteroid_lab/services/placement_goal.py
django_apps/asteroid_lab/services/throughput_target.py
django_apps/asteroid_lab/services/committed_throughput_summary.py
django_apps/asteroid_lab/services/rttp_recovery_evidence.py
django_apps/asteroid_lab/services/rttp_route_connectivity.py
django_apps/asteroid_lab/services/rttp_exterior_transport_resolver.py
django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py
django_apps/asteroid_lab/services/lab_optimization_milestone_payload.py
django_apps/asteroid_lab/services/mining_equipment_goal.py
django_apps/asteroid_lab/services/required_external_connectors.py
```

- [x] **Trim** `lab_replay_timeline_payload.py`, `solver_run_lab_summary.py` — remove optimization imports and RTTP-only code paths; keep reconstruction timeline.

### Task 4c: Management commands

Delete:

```text
django_apps/asteroid_lab/management/commands/capture_rttp_recovery_evidence.py
django_apps/asteroid_lab/management/commands/scan_rttp_slug_certification.py
```

(Any other `*rttp*` commands — `rg rttp django_apps/asteroid_lab/management`.)

### Task 4d: Tests and harness

- [x] **Step 1: Delete test files**

```powershell
Get-ChildItem -Recurse tests -Filter "*rttp*" | Select-Object FullName
Get-ChildItem -Recurse tests -Filter "*optimization*" | Select-Object FullName
```

Delete all unit/integration/investigation RTTP tests. Update `tests/unit/architecture/quarantine_registry.py` per [`2026-05-30-test-cleanup-aggressive-decontamination-design.md`](../specs/2026-05-30-test-cleanup-aggressive-decontamination-design.md) if entries block collection.

- [x] **Step 2: Delete harness**

```text
harness/investigation/rttp_*.py
harness/investigation/run_canon_slug_probe.py
```

### Task 4e: Scripts

```powershell
rg "rttp|run_rttp" scripts --files-with-matches
```

Delete RTTP sweep/evidence scripts; keep `test_reconstruction_narrow.ps1`, `test_capacity_sot.ps1`.

### Task 4f: Fix import fallout

```bash
python -m pytest tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py -v --tb=short
```

Iterate until reconstruction narrow gate green.

```bash
python -m ruff check django_apps/asteroid_lab
python -m mypy django_apps/asteroid_lab
```

### Task 4g: PR-B commit

```bash
git commit -m "feat(asteroid_lab): PR-B remove optimization catalog RTTP runtime"
```

---

## Task 5: PR-B — Doc hygiene (Hybrid C)

**Files:** `docs/superpowers/**`, `documents/archive/asteroid_lab_rttp_retired_2026-05/`

- [x] **Step 1: Hard-delete active RTTP specs**

Delete all `docs/superpowers/specs/*rttp*` **except** keep:

- `2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md`
- `2026-05-26-reconstruction-complete-map-dto-design.md` (normative DTO)
- Optionally keep `2026-05-22-strip-solver-keep-recon-complete-design.md` as historical pointer

Delete: `2026-05-30-rttp-v0-2-core-algorithm-recovery-design.md`, all ELCP/MEG/GA specs, etc.

- [x] **Step 2: Hard-delete ACTIVE/recovery RTTP plans**

Delete `docs/superpowers/plans/*rttp*` with ACTIVE/recovery/evidence recapture in title or body `NEXT:`.

- [x] **Step 3: Archive ≤10 closed milestone plans**

Create `documents/archive/asteroid_lab_rttp_retired_2026-05/plans/` and move e.g.:

- `2026-05-22-strip-solver-keep-recon-complete.md` (executed)
- `2026-05-26-reconstruction-complete-map-dto.md` (if closed)
- Up to 8 other **CLOSED** milestone plans (not ACTIVE forensic)

Front matter on each:

```yaml
---
status: RETIRED_ARCHIVE
do_not_execute: true
superseded_by: docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md
---
```

- [x] **Step 4: Reports — default delete**

```powershell
Remove-Item docs/superpowers/reports/*rttp* -Recurse -Force  # review list first; keep 0-3 summaries only
```

- [x] **Step 5: Archive README + evidence_summary**

Create:

- `documents/archive/asteroid_lab_rttp_retired_2026-05/README.md` — why RTTP removed, pointer to decontamination spec
- `documents/archive/asteroid_lab_rttp_retired_2026-05/evidence_summary.md` — 1-page forensic summary (no large JSON)

- [x] **Step 6: MEG spec/plan remain FROZEN** — do not delete `2026-05-27-rttp-mining-equipment-goal-contract-design.md`

- [x] **Step 7: Commit**

```bash
git add -A docs documents/archive
git commit -m "docs: RTTP hard-delete and selective archive (Hybrid C)"
```

---

## Task 6: Contamination gate inversion

**Files:**
- Create: `tests/unit/architecture/test_reconstruction_decontamination_gates.py`
- Modify: `scripts/test_optimization_contamination.ps1` → rename or replace with `scripts/test_reconstruction_decontamination.ps1`
- Modify: `tests/unit/architecture/test_optimization_contamination_gates.py` — delete or replace

- [x] **Step 1: Write architecture tests**

```python
# tests/unit/architecture/test_reconstruction_decontamination_gates.py
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_OPT = _REPO / "django_apps" / "asteroid_lab" / "optimization"
_RECON = _REPO / "django_apps" / "asteroid_lab" / "reconstruction"


def test_optimization_package_absent():
    assert not _OPT.exists(), "optimization/ must be deleted (GATE-R1)"


def test_reconstruction_imports_no_optimization():
    text = "\n".join(p.read_text(encoding="utf-8") for p in _RECON.rglob("*.py"))
    assert "django_apps.asteroid_lab.optimization" not in text
    assert "django_apps.asteroid_lab.catalog" not in text


def test_no_run_rttp_pipeline_outside_archive():
    import subprocess

    proc = subprocess.run(
        ["rg", "run_rttp_pipeline", "--glob", "!documents/archive/**"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1, proc.stdout  # rg exit 1 = no matches
```

- [x] **Step 2: PowerShell gate owner**

Create `scripts/test_reconstruction_decontamination.ps1`:

```powershell
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pytest tests/unit/architecture/test_reconstruction_decontamination_gates.py -v --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
rg "run_rttp_pipeline" --glob "!documents/archive/**"
if ($LASTEXITCODE -eq 0) { throw "run_rttp_pipeline still referenced" }
exit 0
```

- [x] **Step 3: Update `current_plan.md` standing gates**

Replace PR-B optimization contamination owner with `test_reconstruction_decontamination.ps1`.

- [x] **Step 4: Run gates**

```powershell
powershell -File scripts/test_reconstruction_decontamination.ps1
powershell -File scripts/test_reconstruction_narrow.ps1
powershell -File scripts/test_capacity_sot.ps1
```

- [ ] **Step 5: Scoped ruff**

```bash
python -m ruff check django_apps/asteroid_lab/reconstruction django_apps/asteroid_lab/contracts django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/asteroid_lab/cleanup
```

---

## Task 7: Closeout

- [x] **Step 1: Full gate (pre-merge)**

```powershell
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m mypy django_apps config src
python -m black --check .
```

- [x] **Step 2: `current_plan.md` P0 CLOSED**

After PR-B merge, under P0 banner:

```markdown
**CLOSED (YYYY-MM-DD):** Reconstruction complete-map decontamination — PR #___
```

- [x] **Step 3: MEG remains FROZEN**

Confirm `2026-05-27-rttp-mining-equipment-goal-contract-design.md` status unchanged.

- [x] **Step 4: Decontamination spec status**

Set design spec to **CLOSED (implementation YYYY-MM-DD)** with PR link.

- [ ] **Step 5: `rg rttp` smoke (human)**

```powershell
rg "rttp" docs/superpowers --glob "!documents/archive/**" -c
```

Expected: only decontamination + complete-map DTO + archive pointers.

---

## Plan self-review (2026-05-27)

| Spec section | Task |
|--------------|------|
| Locked direction | Task 0, 7 |
| KEEP slice | Tasks 3–4 (no delete recon) |
| DELETE runtime | Tasks 4, 6 |
| Stub SOLVER_NOT_AVAILABLE | Task 2 |
| Hybrid C docs | Task 5 |
| GATE-R1–R8 | Tasks 3, 6, 7 |
| MEG FROZEN | Tasks 0, 5, 7 |
| shapez_solver out of scope | (implicit — no tasks) |

No TBD steps. PR-A/B split matches spec §7.

---

## Execution handoff

Plan saved. **Forbidden until decontamination merges:** MEG-C2, RTTP implementation, v0.2 recovery.

**Execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session with executing-plans, checkpoints after Task 2 and Task 4

Which approach?
