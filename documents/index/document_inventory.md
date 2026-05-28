# Document Inventory

As of: 2026-05-27 (post P0 decontamination)  
Scope: Major design · plan · research · report · archive documents under `documents/`. Not a full file listing — an authority map for AI context selection.

Status enum follows [`document_lifecycle.md`](document_lifecycle.md).

## Hot path (Asteroid Lab — reconstruction slice only)

1. Code + tests → `django_apps/asteroid_lab/reconstruction/`, `cleanup/`, `replay/`, `services/solver_runtime_entry.py`
2. [`documents/ai/current_plan.md`](../ai/current_plan.md) — runtime + standing gates
3. **Topic row** in § Asteroid Lab authority by topic (below)
4. [`documents/ai/contamination_policy.md`](../ai/contamination_policy.md)
5. Normative superpowers: decontamination + complete-map DTO specs (see table)

**QUARANTINE / ARCHIVE (never implementation authority):**

- [`documents/archive/asteroid_lab_rttp_retired_2026-05/`](../archive/asteroid_lab_rttp_retired_2026-05/) — RTTP runtime retired
- [`documents/plans/asteroid_lab_optimization/`](../plans/asteroid_lab_optimization/) — pre-strip-solver snapshots (if present)

There is no separate `authority_index.md`; this file is the sole authority map.

## Canonical Documents

| Document | Status | Kind | Canonical | Notes |
|------|------|------|-----------|------|
| [`AGENTS.md`](../../AGENTS.md) | `CANON` | workflow spec | YES | Routing · document authority · approval prohibitions |
| [`.cursor/rules/shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc) | `CANON` | rule | YES | Cursor single alwaysApply (Caveman · gates · verification) |
| [`documents/ai/START_HERE.md`](../ai/START_HERE.md) | `CANON` | context entrypoint | YES | AI context selection entry point |
| [`documents/ai/manuals/`](../ai/manuals/) | `CANON` | workflow manuals | YES | On-demand manuals by work type |
| [`documents/ai/contamination_policy.md`](../ai/contamination_policy.md) | `CANON` | governance policy | YES | Contamination patterns · legacy tokens · PR playbook |
| [`documents/index/document_lifecycle.md`](document_lifecycle.md) | `CANON` | document governance | YES | Document status enum and reading priority |
| [`documents/index/document_inventory.md`](document_inventory.md) | `CANON` | document governance | YES | Current document authority map |
| [`documents/adr/`](../adr/) | `CANON` | architecture decisions | YES | Rationale for canonical spec decisions |
| [`documents/game_rules/`](../game_rules/) | `CANON` | domain spec | YES | shapez 2 rules and solver domain abstraction |
| [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../game_rules/shapez2_asteroid_space_transport_throughput.md) | `CANON` | domain throughput | YES | Asteroid Miner/Pump · Space Belt/Pipe absolute L/min · shapes/min |
| [`documents/research/research_blueprint_grid_coordinates_2026-05-10.md`](../research/research_blueprint_grid_coordinates_2026-05-10.md) | `CANON` | domain invariant | YES | blueprint grid coordinate invariant |

## Active Work · Backlog

| Document | Status | Kind | Canonical | Notes |
|------|------|------|-----------|------|
| [`documents/ai/current_plan.md`](../ai/current_plan.md) | `ACTIVE` | work queue | NO | Post-P0 runtime + gates; RTTP queue in archive |
| [`documents/ai/checklist.md`](../ai/checklist.md) | `ACTIVE` | checklist | NO | Progress state and verification gates |
| [`documents/plans/`](../plans/) | `ACTIVE` | plans/backlog | NO | Plans with unconfirmed completion evidence |
| [`documents/ai/plans/`](../ai/plans/) | `ACTIVE` | scoped plans | NO | Scope-limited plans |
| [`documents/Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md`](../Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md) | `ACTIVE` | post-v0 roadmap | NO | Not started baseline; **`current_plan.md` wins** |

## Asteroid Lab authority by topic (post-decontamination)

When two documents disagree on Asteroid Lab implementation, resolve by this table. **Do not merge competing specs.** RTTP / optimization runtime is **retired** — see archive README.

| Topic | `authority_for_implementation` | Inventory status | Notes |
|-------|-------------------------------|------------------|-------|
| Product slice / surgery | [`docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md`](../../docs/superpowers/specs/2026-05-27-asteroid-lab-reconstruction-complete-map-decontamination-design.md) | **CLOSED** | PR #117; `optimization/` deleted |
| Complete-map DTO semantics | [`docs/superpowers/specs/2026-05-26-reconstruction-complete-map-dto-design.md`](../../docs/superpowers/specs/2026-05-26-reconstruction-complete-map-dto-design.md) | CANON | Field-cell SoT |
| Runtime entry / Run Solver | [`current_plan.md`](../ai/current_plan.md) + `solver_runtime_entry.py` | CANON → code | Always `SOLVER_NOT_AVAILABLE`; flag ignored |
| Reconstruction topology | `django_apps/asteroid_lab/reconstruction/` + [`asteroid_lab_00_overview.md`](../Algorithm/asteroid_lab_00_overview.md) | CANON → code | Coordinates · prohibitions |
| Replay timeline (Lab) | [`asteroid_lab_09_replay_timeline.md`](../Algorithm/asteroid_lab_09_replay_timeline.md) | CANON | Reconstruction replay only |
| Lab replay wiring | [`asteroid_lab_12_runtime_replay_wiring.md`](../Algorithm/asteroid_lab_12_runtime_replay_wiring.md) | CANON | Output-only product replay |
| Capacity / mineable SoT | [`docs/superpowers/specs/2026-05-29-reconstruction-capacity-c-gate-design.md`](../../docs/superpowers/specs/2026-05-29-reconstruction-capacity-c-gate-design.md) | ACTIVE | C-GATE on complete map |
| Terrain rim highlight | [`docs/superpowers/specs/2026-05-25-reconstruction-complete-terrain-rim-highlight-design.md`](../../docs/superpowers/specs/2026-05-25-reconstruction-complete-terrain-rim-highlight-design.md) | CLOSED | UI enrichment from complete map |
| Replay boundary | [`docs/superpowers/specs/2026-05-24-b-cs4-reconstruction-replay-boundary-design.md`](../../docs/superpowers/specs/2026-05-24-b-cs4-reconstruction-replay-boundary-design.md) | CLOSED | Reconstruction vs replay |
| Game data snapshot | `django_apps/asteroid_lab/contracts/game_data_snapshot*.py` | CANON → code | Not RTTP catalog contracts |
| MEG contract (frozen) | [`docs/superpowers/specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md`](../../docs/superpowers/specs/2026-05-27-rttp-mining-equipment-goal-contract-design.md) | **FROZEN** | Do not implement until RTTP re-opened |
| RTTP / optimization / routing / commit / GA | [`documents/archive/asteroid_lab_rttp_retired_2026-05/`](../archive/asteroid_lab_rttp_retired_2026-05/) | **RETIRED** | No `optimization/` package |
| Legacy Algorithm 01–08 · solver_runtime phases | [`documents/archive/asteroid_lab_rttp_retired_2026-05/algorithm/`](../archive/asteroid_lab_rttp_retired_2026-05/algorithm/) | **RETIRED** | Historical reference only |
| Mining layout solver (removed) | git history only | **REMOVED** | — |
| `shapez_solver` (factory graph) | `django_apps/shapez_solver/` | OUT OF SCOPE | Not Asteroid Lab decontamination |

**Operational label QUARANTINE:** Maps to lifecycle enum `ARCHIVED` or `SUPERSEDED` plus `do_not_use_as_authority: true` in front matter (see [`document_lifecycle.md`](document_lifecycle.md)).

## Research · Report

| Document | Status | Kind | Canonical | Notes |
|------|------|------|-----------|------|
| [`project_harness_research.md`](../../project_harness_research.md) | `RESEARCH` | harness design | NO | Cursor harness · agent operations design report (root location, 2026-05-19) |
| [`documents/research/`](../research/) | `RESEARCH` | research | NO | Investigation · evidence. Individual docs may be promoted to canonical |
| [`documents/research/research_shapez2_space_transport_throughput_2026-05-18.md`](../research/research_shapez2_space_transport_throughput_2026-05-18.md) | `SUPERSEDED` | game throughput | NO | → [`game_rules/shapez2_asteroid_space_transport_throughput.md`](../game_rules/shapez2_asteroid_space_transport_throughput.md) |
| [`documents/reports/README.md`](../reports/README.md) | `REPORT` | report index | NO | Report bundle routing. Not a canonical contract |
| [`documents/debug/`](../debug/) | `REPORT` | debug report | NO | Log/copy analysis |
| [`documents/notes/`](../notes/) | `REPORT` | notes | NO | Long-term memos. Not canonical |
| [`documents/Algorithm/README.md`](../Algorithm/README.md) | `CANON` | algorithm index | YES | Post-P0 reconstruction-first index |

## Archive · Completed Documents

| Document | Status | Kind | Canonical | Notes |
|------|------|------|-----------|------|
| [`documents/archive/README.md`](../archive/README.md) | `CANON` | archive index | YES | Archive bucket map |
| [`documents/archive/asteroid_lab_rttp_retired_2026-05/README.md`](../archive/asteroid_lab_rttp_retired_2026-05/README.md) | `ARCHIVED` | RTTP retirement | NO | Forensic + retired superpowers |
| [`documents/archive/2026-05-completed/README.md`](../archive/2026-05-completed/README.md) | `COMPLETED` | completed index | NO | 2026-05 completed bundle |
| [`documents/archive/completed-implementation/README.md`](../archive/completed-implementation/README.md) | `COMPLETED` | completed plan/research pairs | NO | Per-stem pairs for completed implementation |
| [`documents/archive/obsolete-src-shapez2-solver-plans-2026-05-01/`](../archive/obsolete-src-shapez2-solver-plans-2026-05-01/) | `ARCHIVED` | obsolete plan set | NO | Pre-Django-first transition plans |
| [`documents/refactory/README.md`](../refactory/README.md) | `ARCHIVED` | redirect | NO | v1-era tree removed. Past body text in git history |

## Next Cleanup Candidates

| Item | Current Status | Action |
|------|----------|------|
| Root `v2_behavior_artifact_*.json` | generated artifact | Separate decision on execution output cleanup |

## Structure Notes

- `django_apps.shapez_asteroid` and `tests/unit/shapez_asteroid*` have been removed.
- `django_apps/asteroid_lab/optimization/` and `catalog/` **removed** (P0 decontamination PR #117).
- Mining layout solver (`documents/Algorithm/mining_solver_cursor_sessions/`) — **git history only**.
- RTTP superpowers specs/plans — moved under [`documents/archive/asteroid_lab_rttp_retired_2026-05/superpowers/`](../archive/asteroid_lab_rttp_retired_2026-05/superpowers/) when filename matched retirement patterns (2026-05-27 G4).
