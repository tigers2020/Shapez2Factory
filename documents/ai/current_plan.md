# Current plan

**CLOSED (2026-05-29, Lab gate green on `master` `f6e62f8e`):** Outer-rim placement + replay — PR [#125](https://github.com/tigers2020/Shapez2Factory/pull/125) L4 sprite domain kinds · [#127](https://github.com/tigers2020/Shapez2Factory/pull/127) L4 mining-first selection · [#128](https://github.com/tigers2020/Shapez2Factory/pull/128) L2 exterior connector replay persistence. **Specs:** [`2026-05-30-outer-rim-direction-arbitration-design.md`](../../docs/superpowers/specs/2026-05-30-outer-rim-direction-arbitration-design.md) · [`2026-05-29-l2-exterior-connector-replay-persistence-design.md`](../../docs/superpowers/specs/2026-05-29-l2-exterior-connector-replay-persistence-design.md). **Deferred:** P1/P2 L3 observability (spec §5) — hold unless direction debugging insufficient.

**CLOSED (2026-05-28):** Miner seed intrinsic difficulty + priority rank — branch `feat/miner-seed-difficulty-rank` (PR-D1/D2/D2b). Spec [`docs/superpowers/specs/2026-05-28-miner-seed-difficulty-rank-design.md`](../../docs/superpowers/specs/2026-05-28-miner-seed-difficulty-rank-design.md) §9. `difficulty_rank` = curriculum; `intrinsic_priority_rank` = gene picker default; `search_priority_rank` deferred Phase 5.

**CLOSED (2026-05-27, merged to `master`):** Reconstruction complete-map decontamination — PR [#117](https://github.com/tigers2020/Shapez2Factory/pull/117). **Spec:** [`docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md`](../../docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md) · **Plan:** [`docs/superpowers/plans/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md`](../../docs/superpowers/plans/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination.md)

| Queue | State |
|-------|--------|
| Outer-rim (#125/#127/#128) | **CLOSED** — Lab gate 2026-05-29 |
| P1/P2 L3 observability (rim) | **HOLD** — after Lab green; reopen only if direction forensics insufficient |
| Lab replay lazy-load (13C POST) | **CLOSED** — [`2026-05-30-lab-replay-lazy-load-post-slimming.md`](../../docs/superpowers/plans/2026-05-30-lab-replay-lazy-load-post-slimming.md) |
| Replay payload 13D-SSR | **IMPLEMENTED (local)** — [`2026-05-29-replay-payload-13d-ssr-slim.md`](../../docs/superpowers/plans/2026-05-29-replay-payload-13d-ssr-slim.md) · spec [`2026-05-29-replay-payload-network-optimization-design.md`](../../docs/superpowers/specs/2026-05-29-replay-payload-network-optimization-design.md) |
| Replay compose defer 13C2-lite | **PR open** — [#131](https://github.com/tigers2020/Shapez2Factory/pull/131) · branch `feat/replay-compose-defer-artifact-reuse` · spec [`2026-05-29-replay-compose-defer-artifact-reuse-design.md`](../../docs/superpowers/specs/2026-05-29-replay-compose-defer-artifact-reuse-design.md) · plan [`2026-05-29-replay-compose-defer-artifact-reuse.md`](../../docs/superpowers/plans/2026-05-29-replay-compose-defer-artifact-reuse.md). Lazy SSR and lab-replay GET reuse persisted composed replay cache on cache-hit paths; GET payload shape unchanged; 13E/13G remain follow-up. **Perf verification (`lab_perf.jsonl`, 2026-05-29, `rttp-core-recovery-test-map`, cache warm):** `project_page` cache-hit `total_ms` ≈ 3,203 · `html_bytes` ≈ 369 KB · `build_lab_replay_frames_for_project_ms` absent · `replay_cache_miss_compose_ms` absent · bottleneck `solver_runs_for_lab_project_ms` ≈ 2,922. `lab_replay_get` cache-hit `total_ms` ≈ 1,297 · `replay_cache_load_ms` ≈ 515 · `json_response_build_ms` ≈ 391 · `replay_compose_ms` absent · `response_bytes` ≈ 15.8 MB unchanged. `run_solver` `total_ms` ≈ 10,469 · `replay_compose_once_ms` ≈ 5,562 · `layer_03_ms` ≈ 2,344 (compose-once by design). **Next:** PR merge, then 13G. |
| Replay payload 13G gzip | **NEXT** — [`2026-05-29-replay-payload-13g-compression.md`](../../docs/superpowers/plans/2026-05-29-replay-payload-13g-compression.md) |
| P0 Decontamination | **CLOSED** — [#117](https://github.com/tigers2020/Shapez2Factory/pull/117) |
| RTTP / v0.2 recovery / MEG-C2 implementation | **RETIRED** — do not implement |
| MEG contract | **FROZEN** — [`2026-05-27-rttp-mining-equipment-goal-contract-design.md`](../../docs/superpowers/specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md) (reference only) |

**Runtime (authoritative):** decode → cleanup → reconstruction → `ReconstructionCompleteMap` → persist → Lab reconstruction replay. `run_solver` / `solver_runtime_entry` → **`SOLVER_NOT_AVAILABLE`** (`ASTEROID_LAB_RTTP_ENABLED` ignored). **`shapez_solver` out of scope.**

**RTTP historical queue:** **hard-deleted** (2026-05-28) — git history only; **do not implement**.

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
```

## Maintenance / Standing Gates

- **Replay narrow:** `scripts/test_reconstruction_narrow.ps1`
- **P0 decontamination:** `scripts/test_reconstruction_decontamination.ps1`
- **Capacity C-GATE:** `scripts/test_capacity_sot.ps1`
- **Quarantine registry:** `scripts/test_quarantine_registry.ps1`

Full gate: [`AGENTS.md`](../../AGENTS.md) · `scripts/test_full.ps1`

## Next focus (implementation queue)

When opening new work, start from [`document_inventory.md`](../index/document_inventory.md) — **no RTTP rows**. **Primary:** Lab replay lazy-load ([`2026-05-30-lab-replay-lazy-load-post-slimming.md`](../../docs/superpowers/plans/2026-05-30-lab-replay-lazy-load-post-slimming.md)). **Maintenance:** Capacity C-GATE, PR-F test cleanup follow-ons.
