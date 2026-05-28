# Asteroid Lab RTTP runtime — retired archive (2026-05)

RTTP optimization runtime (`django_apps/asteroid_lab/optimization/`, `catalog/`, placement/routing/commit pipeline, and related tests) was **removed** in the P0 decontamination program.

## Authoritative replacement

- **Spec:** [`docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md`](../../docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md)
- **Implementation plan:** [`docs/superpowers/plans/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md`](../../docs/superpowers/plans/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md)
- **Product slice kept:** reconstruction through `ReconstructionCompleteMap`, Lab reconstruction replay shell, capacity SoT on complete-map field cells.
- **Solver entry:** `run_solver` / HTTP run-solver return `SOLVER_NOT_AVAILABLE` (fail-closed stub).

## What lives here

- `plans/` — selected **closed** milestone plans from the RTTP era (historical only; `do_not_execute: true`).
- `superpowers/` — retired RTTP specs/plans/reports moved from active `docs/superpowers/` (G4 hygiene 2026-05-27).
- `algorithm/` — legacy `asteroid_lab_01`–`08`, `solver_runtime/` phase series.
- [`current_plan_rttp_historical.md`](current_plan_rttp_historical.md) — full RTTP queue + closed forensic rows (extracted from `current_plan.md`).
- [`evidence_summary.md`](evidence_summary.md) — one-page forensic summary (no large JSON artifacts).

## Frozen references (active tree — read-only)

- [`docs/superpowers/specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md`](../../docs/superpowers/specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md) — **FROZEN**; do not implement MEG-C2 until RTTP is explicitly re-opened.
- [`superpowers/plans/2026-05-27-rttp-mining-equipment-goal.md`](superpowers/plans/2026-05-27-rttp-mining-equipment-goal.md) — **DO NOT EXECUTE** (archived plan).

## Do not

- Re-implement RTTP from archived plans without a new approved spec.
- Use archived paths as import targets (`optimization/` and `catalog/` packages no longer exist).
