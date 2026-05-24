# Document Inventory

As of: 2026-05-24  
Scope: Major design · plan · research · report · archive documents under `documents/`. Not a full file listing — an authority map for AI context selection.

Status enum follows [`document_lifecycle.md`](document_lifecycle.md).

## Hot path (Asteroid Lab / RTTP)

1. Code + tests → [`documents/ai/current_plan.md`](../ai/current_plan.md)
2. **Topic row** in § Asteroid Lab authority by topic (below) — **conflict resolver**
3. Row-designated spec or Algorithm doc
4. [`documents/ai/contamination_policy.md`](../ai/contamination_policy.md)

**QUARANTINE (never implementation authority):** [`documents/plans/asteroid_lab_optimization/`](../plans/asteroid_lab_optimization/)

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
| [`documents/ai/current_plan.md`](../ai/current_plan.md) | `ACTIVE` | work queue | NO | Current work flow |
| [`documents/ai/checklist.md`](../ai/checklist.md) | `ACTIVE` | checklist | NO | Progress state and verification gates |
| [`documents/plans/`](../plans/) | `ACTIVE` | plans/backlog | NO | Plans with unconfirmed completion evidence. **Exception:** `plans/asteroid_lab_optimization/` = **QUARANTINE** — see § Asteroid Lab authority by topic |
| [`documents/ai/plans/`](../ai/plans/) | `ACTIVE` | scoped plans | NO | Scope-limited plans |
| [`documents/Algorithm/solver_runtime/`](../Algorithm/solver_runtime/) | `HISTORICAL` | solver button pipeline | NO | Phase A–M orchestration archive. **RTTP runtime ≠ this series** — [`current_plan.md`](../ai/current_plan.md) is canonical |
| [`documents/Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md`](../Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md) | `ACTIVE` | post-v0 roadmap | NO | 2026-05-18 spec · checklist not started baseline; **do not compare** against v0 completion — [`current_plan.md`](../ai/current_plan.md) takes precedence |

## Asteroid Lab authority by topic

When two documents disagree on Asteroid Lab / RTTP implementation, resolve by this table. **Do not merge competing specs.**

| Topic | `authority_for_implementation` | Inventory status | Notes |
|-------|-------------------------------|------------------|-------|
| Runtime entry / config gate | [`current_plan.md`](../ai/current_plan.md) + `django_apps/asteroid_lab/services/solver_runtime_entry.py` | CANON → code | `ASTEROID_LAB_RTTP_ENABLED`; strip removed monolith only |
| RTTP Hybrid C pipeline | [`docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md`](../../docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md) + `django_apps/asteroid_lab/optimization/` | ACTIVE spec | Merged baseline on `master` |
| Macro bundle T3 | [`docs/superpowers/specs/2026-05-23-rttp-v1-macrobundle-t3-design.md`](../../docs/superpowers/specs/2026-05-23-rttp-v1-macrobundle-t3-design.md) | ACTIVE spec | **PAUSE** per `current_plan` — no new macro work |
| B2 catalog slice / transport T2 | [`docs/superpowers/specs/2026-05-24-b2-t2-per-cell-transport-resolution-design.md`](../../docs/superpowers/specs/2026-05-24-b2-t2-per-cell-transport-resolution-design.md) | CLOSED | PR #62; tests ground truth |
| B2 transport-aware route domain T3 | [`docs/superpowers/specs/2026-05-24-b2-t3-transport-aware-route-domain-design.md`](../../docs/superpowers/specs/2026-05-24-b2-t3-transport-aware-route-domain-design.md) | CLOSED | PR #61 |
| Track D footprint/connector | [`docs/superpowers/specs/2026-05-24-building-catalog-slice-first-consumption-design.md`](../../docs/superpowers/specs/2026-05-24-building-catalog-slice-first-consumption-design.md) | ACTIVE | Design parent; plan TBD |
| OptimizationInput / adapter | [`documents/Algorithm/asteroid_lab_01_optimization_input.md`](../Algorithm/asteroid_lab_01_optimization_input.md) | CANON | **Not** `plans/asteroid_lab_optimization/01` |
| Route probe / candidate pool | [`documents/Algorithm/asteroid_lab_04_route_probe.md`](../Algorithm/asteroid_lab_04_route_probe.md) | CANON | Probe at creation |
| Validation read-only | [`documents/Algorithm/asteroid_lab_08_validation.md`](../Algorithm/asteroid_lab_08_validation.md) + [`documents/adr/ADR-003-final-validation-assertion-gate.md`](../adr/ADR-003-final-validation-assertion-gate.md) | CANON | |
| Replay timeline / 3B-S | [`documents/Algorithm/asteroid_lab_09_replay_timeline.md`](../Algorithm/asteroid_lab_09_replay_timeline.md) + [`docs/superpowers/specs/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md`](../../docs/superpowers/specs/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md) | CANON + ACTIVE spec | Output-only product replay |
| Development sequence | [`documents/Algorithm/asteroid_lab_10_development_sequence.md`](../Algorithm/asteroid_lab_10_development_sequence.md) + `current_plan` RTTP gate sync | ACTIVE doc | Checkbox state may lag; gate sync note wins |
| Pre-RTTP plans tree | [`documents/plans/asteroid_lab_optimization/`](../plans/asteroid_lab_optimization/) | **QUARANTINE** (`ARCHIVED`) | `do_not_use_as_authority: true` |
| Solver runtime Phase A–M | [`documents/Algorithm/solver_runtime/`](../Algorithm/solver_runtime/) | **HISTORICAL** | Orchestration archive; RTTP ≠ this series |
| Mining layout solver (removed) | git history only | **REMOVED** | No START_HERE table |
| Lab replay wiring | [`documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md`](../Algorithm/asteroid_lab_12_runtime_replay_wiring.md) | CANON | Distinct from optimization search |

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
| [`documents/Algorithm/README.md`](../Algorithm/README.md) | `RESEARCH` | algorithm memos index | NO | Asteroid Lab optimization series · drafts (`drafts/`). Entry README. Implementation canonical is code · CANON first |

## Archive · Completed Documents

| Document | Status | Kind | Canonical | Notes |
|------|------|------|-----------|------|
| [`documents/archive/README.md`](../archive/README.md) | `CANON` | archive index | YES | Archive bucket map |
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
- Mining layout solver canonical step spec (`documents/Algorithm/mining_solver_cursor_sessions/`) and related archive/plan bulk cleanup remain in **git history** only.
- `documents/plans/asteroid_lab_optimization/` tree is a pre-strip-solver plan snapshot. **QUARANTINE** — not implementation canonical. RTTP runtime is `django_apps/asteroid_lab/optimization/` + [`current_plan.md`](../ai/current_plan.md).
