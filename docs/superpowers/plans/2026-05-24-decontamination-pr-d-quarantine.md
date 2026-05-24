# Decontamination PR-D — Quarantine & Stale Path Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add two-tier quarantine registry + architecture gates; no production or deletion changes.

**Architecture:** `QUARANTINED_MODULE_PREFIXES` for AST checks on bounded active-runtime roots; `QUARANTINED_DOC_PATHS` for front-matter disposition; `PR_E_DELETE_CANDIDATES` declared only (PR-E deletes).

**Tech Stack:** Python 3.12+, ast, pytest, ruff, PowerShell standing script.

**Spec:** [`../specs/2026-05-24-decontamination-pr-d-quarantine-design.md`](../specs/2026-05-24-decontamination-pr-d-quarantine-design.md)

---

## File map

| File | Action |
|------|--------|
| `tests/unit/architecture/quarantine_registry.py` | Create — two-tier registry |
| `tests/unit/architecture/test_quarantined_paths_do_not_leak.py` | Create — 5 tests |
| `scripts/test_quarantine_registry.ps1` | Create — standing gate |
| `documents/plans/asteroid_lab_optimization/*.md` | Modify — YAML front matter |
| `documents/Algorithm/solver_runtime/README.md` | Modify — `do_not_use_as_authority` |
| `documents/ai/current_plan.md` | Modify — PR-D ACTIVE / CLOSED |
| `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | Modify |

**Do not delete** `test_service_import_boundaries.py` in PR-D.

---

## Task 0 — Baseline verification record

Recorded on `master` @ `9e70d169`: reconstruction 55, RTTP narrow 127, PR-B standing 4.

---

## Tasks 1–7

Implemented on `feat/decontamination-pr-d-quarantine`:

- Task 1: `quarantine_registry.py` with `QUARANTINED_MODULE_PREFIXES`, `QUARANTINED_DOC_PATHS`, `PR_E_DELETE_CANDIDATES`, `ACTIVE_RUNTIME_ROOTS`, `MAX_TRANSITIVE_IMPORT_DEPTH=2`
- Task 2–3: `test_quarantined_paths_do_not_leak.py` (5 tests per spec)
- Task 4: `scripts/test_quarantine_registry.ps1`
- Task 5: docs + front matter sweep (11 plan files + solver_runtime README)
- Task 6: `pytest` + `ruff` green
- Task 7: controller self-review — PR-D does not delete; does not rglob optimization/**

---

## Verification

```powershell
powershell -File scripts/test_quarantine_registry.ps1
powershell -File scripts/test_optimization_contamination.ps1
powershell -File scripts/test_reconstruction_narrow.ps1
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" --tb=short
```
