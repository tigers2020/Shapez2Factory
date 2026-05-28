# Algorithm Documentation

**Post-P0 (2026-05-27):** Asteroid Lab **reconstruction slice only**. RTTP / optimization docs were **hard-deleted** from the repo (2026-05-28); use git history if needed.

**Implementation authority:** code, [`documents/index/document_inventory.md`](../index/document_inventory.md), [`documents/ai/START_HERE.md`](../ai/START_HERE.md).

## Implementation baseline

| Layer | Status | Code / doc |
|--------|------|------|
| **Reconstruction** | **ACTIVE** | `django_apps/asteroid_lab/reconstruction/`, `cleanup/`, Lab persist·replay |
| **Complete-map DTO** | **ACTIVE** | [`docs/superpowers/specs/2026-05-26-reconstruction-complete-map-dto-design.md`](../../docs/superpowers/specs/2026-05-26-reconstruction-complete-map-dto-design.md) |
| **Optimization / RTTP** | **RETIRED** | Archive only — no `optimization/` package |
| **Run Solver** | **STUB** | `SOLVER_NOT_AVAILABLE` — solver_runtime docs removed (git history) |
| **Genetic sample (admin)** | **ACTIVE** | `django_apps/asteroid_lab/genetic_sample/` |

**Surgery specs:** [`2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md`](../../docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md) · [`2026-05-22-strip-solver-keep-recon-complete-design.md`](../../docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md)

## Reading order (reconstruction-first)

1. [`asteroid_lab_00_overview.md`](asteroid_lab_00_overview.md) — coordinates, prohibitions
2. Reconstruction code + [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md)
3. [`asteroid_lab_12_runtime_replay_wiring.md`](asteroid_lab_12_runtime_replay_wiring.md) — Lab JSON wiring
4. **Retired optimization series** — removed from repo (`asteroid_lab_01`–`08`, `10`, `solver_runtime/`, `mining_installation/`); git history only

## Active files (this directory)

| File | Status | Description |
|------|------|------|
| `asteroid_lab_00_overview.md` | `CANON` | Lab·coordinate principles |
| `asteroid_lab_09_replay_timeline.md` | `CANON` | Lab Step Replay Timeline |
| `asteroid_lab_10_development_sequence.md` | `RETIRED` | removed — git history only |
| `asteroid_lab_11_future_execution_plan_post_sequence.md` | `ACTIVE` | Post-sequence roadmap (not started) |
| `asteroid_lab_12_runtime_replay_wiring.md` | `CANON` | Runtime replay wiring |
| `asteroid_lab_13_replay_payload_scalability.md` | `ACTIVE` | Payload / lazy-load contracts |
| [`asteroid_lab_mining_installation/`](asteroid_lab_mining_installation/) | `AUDIT` | Miner·extension authority tables |

## Drafts (`drafts/`)

Non-canonical memos only. Do not use for implementation.

## Path notes

- `django_apps/shapez_asteroid` · `asteroid_lab/optimization/` · `catalog/` — **removed**
- Cross-check: [`documents/index/document_inventory.md`](../index/document_inventory.md)
