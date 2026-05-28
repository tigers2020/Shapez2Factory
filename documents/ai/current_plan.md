# Current plan

**CLOSED (2026-05-27, merged to `master`):** Reconstruction complete-map decontamination — PR [#117](https://github.com/tigers2020/Shapez2Factory/pull/117). **Spec:** [`docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md`](../../docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md) · **Plan:** [`docs/superpowers/plans/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md`](../../docs/superpowers/plans/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md)

| Queue | State |
|-------|--------|
| P0 Decontamination | **CLOSED** — [#117](https://github.com/tigers2020/Shapez2Factory/pull/117) |
| RTTP / v0.2 recovery / MEG-C2 implementation | **RETIRED** — do not implement |
| MEG contract | **FROZEN** — [`2026-05-27-rttp-mining-equipment-goal-contract-design.md`](../../docs/superpowers/specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md) (reference only) |

**Runtime (authoritative):** decode → cleanup → reconstruction → `ReconstructionCompleteMap` → persist → Lab reconstruction replay. `run_solver` / `solver_runtime_entry` → **`SOLVER_NOT_AVAILABLE`** (`ASTEROID_LAB_RTTP_ENABLED` ignored). **`shapez_solver` out of scope.**

**RTTP historical queue:** [`documents/archive/asteroid_lab_rttp_retired_2026-05/current_plan_rttp_historical.md`](../archive/asteroid_lab_rttp_retired_2026-05/current_plan_rttp_historical.md) — forensic only; **do not implement**.

## Authority precedence

Follow [`document_inventory.md`](../index/document_inventory.md) **§ Asteroid Lab authority by topic**.

1. Code: `django_apps/asteroid_lab/reconstruction/`, `cleanup/`, `replay/`, `contracts/game_data_snapshot*.py`, `services/solver_runtime_entry.py`
2. This file — runtime + standing gates
3. Active superpowers specs (decontamination, complete-map DTO, capacity C-GATE, rim, B-CS4)
4. `documents/Algorithm/asteroid_lab_00_overview.md`, `09_replay_timeline.md`, `12_runtime_replay_wiring.md`
5. `documents/archive/` — **not** implementation authority

## ACTIVE code paths

```text
django_apps/asteroid_lab/reconstruction/          ← sole algorithm slice
django_apps/asteroid_lab/cleanup/
django_apps/asteroid_lab/replay/
django_apps/asteroid_lab/contracts/               ← game_data snapshot only
django_apps/asteroid_lab/genetic_sample/          ← admin templates (non-runtime)
django_apps/asteroid_lab/services/solver_runtime_entry.py  ← SOLVER_NOT_AVAILABLE stub
```

**Absent (GATE-R1):** `optimization/`, `catalog/`, `lab_rttp_snapshot_compose.py`, RTTP tests.

## Verification (narrow)

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
powershell -File scripts/test_reconstruction_decontamination.ps1
powershell -File scripts/test_capacity_sot.ps1
powershell -File scripts/test_doc_rttp_retired.ps1
```

## Maintenance / Standing Gates

- **Replay narrow:** `scripts/test_reconstruction_narrow.ps1`
- **P0 decontamination:** `scripts/test_reconstruction_decontamination.ps1`
- **Capacity C-GATE:** `scripts/test_capacity_sot.ps1`
- **Doc RTTP retirement:** `scripts/test_doc_rttp_retired.ps1`
- **Quarantine registry:** `scripts/test_quarantine_registry.ps1`

Full gate: [`AGENTS.md`](../../AGENTS.md) · `scripts/test_full.ps1`

## Next focus (implementation queue)

When opening new work, start from [`document_inventory.md`](../index/document_inventory.md) — **no RTTP rows**. Candidate tracks (non-RTTP): Capacity C-GATE maintenance, Lab replay lazy-load (if not merged), PR-F test cleanup follow-ons.
