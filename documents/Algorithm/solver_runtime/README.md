---
status: ARCHIVED
do_not_use_as_authority: true
owner: solver-runtime-pipeline
last_reviewed: 2026-05-22
archived_reason: Solver optimization pipeline removed; reconstruction-only (see docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md)
---

# Solver Runtime — Solver Button Pipeline

> **Runtime authority (2026-05-24):** Active solver is **RTTP Hybrid C** in `django_apps/asteroid_lab/optimization/` when `ASTEROID_LAB_RTTP_ENABLED=True` — see [`documents/ai/current_plan.md`](../../ai/current_plan.md). This directory documents the **historical Solver-button Phase A–M** orchestration series, not the RTTP implementation contract.

**Role:** Solver Runtime Pipeline Architect  
**Purpose:** Fix the **E2E pipeline v0** contract·PR checklist executed when the UI `Solver` / `Run Solver` button is clicked.

> **Document identity:** **「Solver Button v0 reimplementation·orchestration plan」** — does not mean optimization is absent from the entire repository.  
> **Conflict resolution:** [`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) (package·GA·terminology·PR vs code·replay).  
> **Implementation canonical:** code·`CANON` take priority. This series is `ACTIVE` / `RESEARCH` in nature.  
> **Legacy:** [`asteroid_lab_*`](../) — GA·`BundlePattern`·`shapez_asteroid` paths are **reference**; Solver button merge order is [`implementation_sequence.md`](implementation_sequence.md). Does **not** replace [`asteroid_lab_10`](../asteroid_lab_10_development_sequence.md).

## Execution order vs implementation (PR) order

| Category | Order | Purpose |
|------|------|------|
| **Runtime execution** | A→B→C→D→E→F→G→H→I→J→K→L→M | Orchestration on one button click |
| **Implementation (PR)** | PR1→PR1B→PR2.5→PR2→…→PR7 | Merge·review unit ([`implementation_sequence.md`](implementation_sequence.md)) |

PR1 completing Phase **D** first is for fixing the gene contract; at execution time D comes after C and before E.

## Pipeline summary

```text
DB reconstruction map
→ OptimizationInput
→ capacity / RouteGoal planning
→ GeneTemplate projection
→ geometry validation
→ route probe
→ candidate pool
→ selection
→ incremental commit
→ route materialization
→ validation
→ replay / UI payload
```

**Core invariant:** Candidate generation is search only; **incremental commit alone** creates confirmed layout. Details: [`00_core_principles.md`](00_core_principles.md).

## Reading order

1. [`00_core_principles.md`](00_core_principles.md) — forbidden·allowed·adapter field normalization  
2. [`01_entry_point.md`](01_entry_point.md) — trigger·input/output  
3. [`phase_a_load_reconstruction.md`](phase_a_load_reconstruction.md) ~ [`phase_m_persist_replay_ui.md`](phase_m_persist_replay_ui.md) — Phase A–M  
4. [`implementation_sequence.md`](implementation_sequence.md) — PR1–7 checklist·required tests  
5. [`open_decisions.md`](open_decisions.md)  
6. [`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) — legacy·code·PR status conflict resolution — OD-1–4

## PR ↔ Phase table (historical — removed 2026-05-22)

2026-05-22 strip surgery **deleted PR1–7 code·entire `optimization/` package**. Phase documents are `ARCHIVED` archive.

| PR | Phase | Document |
|----|-------|------|
| PR1–7 | A–M | `phase_*.md` — [`strip-solver spec`](../../../docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md) |

**Retained:** reconstruction (`phase_a` load concept moved to `reconstruction/`), Lab replay ([`asteroid_lab_09_replay_timeline.md`](../asteroid_lab_09_replay_timeline.md)), genetic sample admin.

## Relationship to legacy series

| Topic | Runtime canonical | Legacy reference |
|------|--------------|-------------|
| OptimizationInput·route_domain | phase_b, §0.3 | [`asteroid_lab_01`](../asteroid_lab_01_optimization_input.md) |
| Pattern/gene | phase_d (`GeneTemplate`) | [`asteroid_lab_02`](../asteroid_lab_02_pattern_library.md) (`BundlePattern`) |
| Route probe | phase_g | [`asteroid_lab_04`](../asteroid_lab_04_route_probe.md) |
| Commit / validation / replay | phase_j, l, m | [`asteroid_lab_07`](../asteroid_lab_07_incremental_commit.md) ~ [`09`](../asteroid_lab_09_replay_debug.md), [`12`](../asteroid_lab_12_runtime_replay_wiring.md) |
| GA·evolution | **v0 unused** (greedy only) | [`asteroid_lab_05`](../asteroid_lab_05_genome_fitness.md), [`06`](../asteroid_lab_06_evolutionary_search.md) — legacy reference |

## Throughput CANON

Saturation·goal count calculation: [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md).

## Final Runtime Contract (15 steps) — REMOVED 2026-05-22

> The steps below are the **deleted** optimization pipeline historical contract. Current `Run Solver` → `SOLVER_NOT_AVAILABLE` only.

When Solver button was pressed (historical):

```text
1. Load DB reconstruction map.
2. Convert to OptimizationInput.
3. Treat shape/fluid field kinds as mineable field through sets, not direct kind checks.
4. Estimate platform capacity and required RouteGoal count.
5. Create multiple external RouteGoals without installing transport.
6. Load GeneTemplates.
7. Project every gene against rim anchors and rotations.
8. Validate geometry.
9. Probe route from route_probe_start to planned RouteGoals.
10. Build reachable-only CandidatePool.
11. Select candidates with capacity-aware v0 scorer.
12. Incrementally commit with latest-domain re-probe.
13. Materialize shared route network into belt/pipe sprites.
14. Run read-only validation.
15. Persist result and optimization replay payload.
```

```text
Candidate generation explores possibilities.
Only incremental commit creates confirmed layout.
```

## Code packages — immediately after 2026-05-22 strip (HISTORICAL)

> **HISTORICAL:** The diagram below is the state immediately after strip-solver. **Current canonical** is [`documents/ai/current_plan.md`](../../ai/current_plan.md) — `optimization/` was **restored** as RTTP Hybrid C.

```text
django_apps/asteroid_lab/reconstruction/   ← ACTIVE (topology, complete)
django_apps/asteroid_lab/contracts/        ← game_data snapshot DTOs
django_apps/asteroid_lab/genetic_sample/     ← admin gene templates
django_apps/asteroid_lab/services/solver_runtime_entry.py  ← (2026-05-22) SOLVER_NOT_AVAILABLE stub
django_apps/asteroid_lab/optimization/       ← (2026-05-22) REMOVED
```

### Code packages — current 2026-05-24 (RTTP)

```text
django_apps/asteroid_lab/reconstruction/                       ← ACTIVE
django_apps/asteroid_lab/contracts/                            ← game_data snapshot DTOs
django_apps/asteroid_lab/genetic_sample/                       ← admin gene templates (non-runtime)
django_apps/asteroid_lab/services/solver_runtime_entry.py      ← RTTP runtime entry (config-gated)
django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py ← 3B-S product timeline projection
django_apps/asteroid_lab/optimization/                         ← RTTP Hybrid C (ACTIVE)
```

HTTP `POST …/run-solver/` is retained; immediately after strip the body was a stub. Currently returns RTTP runtime response ([`01_entry_point.md`](01_entry_point.md), [`current_plan.md`](../../ai/current_plan.md)).

---

## RTTP pipeline status (2026-05-24)

> **Note:** Frontmatter `ARCHIVED` above is **historical** (2026-05-22 strip surgery). Current `master` runs **RTTP Hybrid C** when `ASTEROID_LAB_RTTP_ENABLED=True`. Code canonical: [`documents/ai/current_plan.md`](../../ai/current_plan.md).

### Track B2-T2: Per-Cell Transport Resolution (CLOSED — PR #62)

> **Plan:** [`2026-05-24-b2-t2-per-cell-transport-resolution.md`](../../../docs/superpowers/plans/2026-05-24-b2-t2-per-cell-transport-resolution.md)  
> **Spec:** [`2026-05-24-b2-t2-per-cell-transport-resolution-design.md`](../../../docs/superpowers/specs/2026-05-24-b2-t2-per-cell-transport-resolution-design.md)

- [x] **Task 1** — `catalog_transport_policy`: lookup + `resolve_cell_transport_kind` (duplicate same-kind last-wins; conflicting kinds fail-closed)
- [x] **Task 2** — `reconstruction_adapter._existing_transport` T2 wire (`lookup` once; `coord=` on policy API)
- [x] **Task 3** — `docs/domain/asteroid_game_data_snapshot.md` T2 paragraph + parent B2 spec cross-link
- [x] **Task 4** — `test_catalog_consumption_boundaries`, catalog/entry transport tests, reconstruction narrow gate, ruff (B2-T2 paths)
- [x] **Task 5** — Ops smoke B (`copy-import-495e552c`, post-merge)

### Track B2-T3: Transport-Aware Route Domain (CLOSED — PR #61)

> **Plan:** [`2026-05-24-b2-t3-transport-aware-route-domain.md`](../../../docs/superpowers/plans/2026-05-24-b2-t3-transport-aware-route-domain.md)  
> **Spec:** [`2026-05-24-b2-t3-transport-aware-route-domain-design.md`](../../../docs/superpowers/specs/2026-05-24-b2-t3-transport-aware-route-domain-design.md)

- [x] **Task 1–4** — `partition_existing_transport`, adapter `blocked_incompatible_transport_cells`, skeleton/route-domain trunk subtract + blocked union, pipeline metrics
- [x] **Task 5** — domain doc + `current_plan` (see repo `documents/ai/current_plan.md`)
- [x] **Ops smoke C** — `test_rttp_transport_kind_route_domain.py` + mixed adapter partition test (mixed-kind real-map `run_solver` is OPS `copy-import` class where transport is 0 — topology strips transport pre-adapter)

**Next track:** Track D catalog footprint/connector — [`building-catalog-slice-first-consumption-design.md`](../../../docs/superpowers/specs/2026-05-24-building-catalog-slice-first-consumption-design.md) (brainstorming / plan TBD).
