# RTTP decontamination — evidence summary (forensic, one page)

**Date:** 2026-05-27  
**Program:** Asteroid Lab reconstruction complete-map decontamination (P0)  
**Outcome:** RTTP runtime hard-deleted; reconstruction slice preserved.

## Why RTTP was removed

- Product scope narrowed to **reconstruction → `ReconstructionCompleteMap` → Lab replay/capacity UI**.
- RTTP/optimization runtime (`optimization/`, `catalog/`, placement, routing, commit, GA, MEG implementation) was high-churn, test-heavy, and blocked a stable reconstruction-only product path.
- `run_solver` could not remain half-wired: PR-A stub (`SOLVER_NOT_AVAILABLE`, flag-ignored), then PR-B package deletion.

## What was deleted (code)

| Area | Action |
|------|--------|
| `django_apps/asteroid_lab/optimization/` | Hard delete |
| `django_apps/asteroid_lab/catalog/` | Hard delete |
| RTTP contracts, catalog adapters, RTTP services/commands | Hard delete |
| `tests/**/*rttp*`, optimization unit tests, RTTP harness | Hard delete |
| Active RTTP specs/plans/reports under `docs/superpowers/` | Hard delete (Hybrid C) |

## What was kept

| Area | Reason |
|------|--------|
| `reconstruction/**`, `cleanup/**`, recon replay | Product slice |
| `contracts/game_data_snapshot*.py`, `building_catalog_slice.py` | Game data + slice SoT |
| `solver_runtime_entry.py` stub | Fail-closed HTTP/CLI entry |
| Decontamination + complete-map DTO specs | Normative SoT |
| MEG contract/plan | **FROZEN** historical only |

## Verification gates (post PR-B)

- `scripts/test_reconstruction_narrow.ps1` — PASS  
- `scripts/test_capacity_sot.ps1` — PASS  
- GATE-R6: `reconstruction/**` has zero `optimization` imports  
- Stub tests: `ASTEROID_LAB_RTTP_ENABLED=True` still returns `SOLVER_NOT_AVAILABLE`

## Large artifacts

Bulk JSON certification/recovery reports under `docs/superpowers/reports/*rttp*` were removed in doc hygiene. Regenerate from git history if forensic replay is needed.

## Re-open criteria

RTTP or MEG-C2 may return only after a **new approved spec** superseding this decontamination design and an explicit queue decision in `documents/ai/current_plan.md`.
