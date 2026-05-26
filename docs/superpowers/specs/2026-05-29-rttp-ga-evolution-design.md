# RTTP GA Evolution — Design Spec

**Date:** 2026-05-29  
**Status:** Approved for implementation planning (B → A rollout)  
**Owner:** asteroid-lab / RTTP Layer 3 (selection)  
**Track:** v0.1 GA promotion — post Capacity C-GATE CLOSED ([#94](https://github.com/tigers2020/Shapez2Factory/pull/94) `ec1b6a26`)  
**Parent:** [`2026-05-22-rttp-hybrid-c-layout-design.md`](2026-05-22-rttp-hybrid-c-layout-design.md) Layer 3 · [`documents/Algorithm/asteroid_lab_05_genome_fitness.md`](../../../documents/Algorithm/asteroid_lab_05_genome_fitness.md)  
**Implementation plan:** PR-GA-1 [`../plans/2026-05-29-rttp-ga-evolution.md`](../plans/2026-05-29-rttp-ga-evolution.md) (CLOSED) · PR-GA-2 [`../plans/2026-05-29-rttp-ga-evolution-pr-ga-2.md`](../plans/2026-05-29-rttp-ga-evolution-pr-ga-2.md) (pending approval)  
**Queue:** [`documents/ai/current_plan.md`](../../../documents/ai/current_plan.md)

**Related (patterns):**

- [`2026-05-24-deferred-commit-retry-shadow-pr1-design.md`](2026-05-24-deferred-commit-retry-shadow-pr1-design.md) — observe-only shadow step pattern
- [`2026-05-29-reconstruction-capacity-c-gate-design.md`](2026-05-29-reconstruction-capacity-c-gate-design.md) — CLOSED; complete-map SoT for fitness inputs

---

## §1 — Problem and goal

### Problem

v0.1 ships **greedy-regret** as the sole production selector (`select_genome` in `greedy_regret.py`). Hybrid C and `asteroid_lab_05` describe **genome-based evolutionary search**, but no GA runs in the pipeline. Throughput and placement goals (PR-2c/2d) need a path to improve bundle **ordering** without reopening candidate generation, route probe, or commit contracts.

### Goal

```text
Introduce bounded evolutionary selection as an observe-only shadow (PR-GA-1),
then optional config-gated primary selector (PR-GA-2).
```

### Rollout (approved)

| Phase | Mode | Commit authority |
|-------|------|------------------|
| **PR-GA-1** | **Shadow-first (B)** | **greedy-regret** only |
| **PR-GA-2** | **Config-gated swap (A)** | `selection.mode=greedy_regret` (default) \| `evolution` |

---

## §2 — Normative contracts (all phases)

### Input boundary

```text
Evolutionary search consumes ONLY the route-feasible normal candidate pool
(output of candidate generation + immediate route probe).
```

### Forbidden (GA / shadow)

```text
- Generate new BundleCandidate rows or mutate occupied_cells
- Call probe_route or rebuild route_domain for fitness
- Use commit-time re-probe results as fitness input
- Read replay / solver_summary / NDJSON as algorithm input
- Change validation_passed, CommitResult, or route reservations in PR-GA-1
- Run GA on macro pipeline in PR-GA-1 (normal path only)
```

### Allowed

```text
- Genome = ordered subset of candidate_id (PlacementGenome.commit_order shape)
- Fitness from candidate-phase fields: throughput_factor, route_probe_cost,
  route_probe reachable flag, occupied_cells, anchor_coord, output_dir
- Shadow writes algorithm_steps metrics only (output-only)
```

### Commit authority (PR-GA-1)

```text
primary_genome = select_genome(...)   # greedy-regret — unchanged
incremental_commit(primary_genome, ...)  # unchanged
shadow runs after primary selection, before commit; does NOT replace primary_genome
```

### Commit authority (PR-GA-2)

```text
When selection.mode == "evolution":
  primary_genome = select_genome_evolution(...)
Else:
  primary_genome = select_genome(...)   # greedy-regret default
incremental_commit(primary_genome, ...)  # same commit layer
```

Final route proof remains **incremental commit** with latest `route_domain` re-probe per candidate.

---

## §3 — PR-GA-1 scope (shadow-first)

### In scope

- `GaEvolutionShadowConfig` + `GaEvolutionShadowSummary` contracts
- Pure `run_ga_evolution_shadow(...)` — bounded GA on normal pool
- Shared genome fitness evaluator (probe-time scores; overlap / FOT layout constraints)
- Pipeline step `rttp.ga_evolution_shadow` after `rttp.genome_selection`, **before** `incremental_commit`
- `RttpAlgorithmStepId.RTTP_GA_EVOLUTION_SHADOW`
- Unit tests + narrow RTTP regression (shadow enabled fixture)
- `config_json.ga_evolution_shadow` mapper (fail-closed booleans/ints; default **disabled** for runtime cost)
- `current_plan` ACTIVE row for PR-GA-1

### Out of scope (PR-GA-1)

| Item | Phase |
|------|-------|
| `selection.mode` swap | PR-GA-2 |
| Macro pipeline GA | Later |
| LNS / deferred retry behavior change | — |
| Validation repair | — |
| New replay overlay geometry (metrics JSON only) | PR-GA-1 |

### Shadow invariants

| ID | Invariant |
|----|-----------|
| INV-GA1-01 | Shadow must not change `PlacementGenome` used by `incremental_commit`. |
| INV-GA1-02 | Shadow runs after greedy `select_genome`, before `incremental_commit`. |
| INV-GA1-03 | No `probe_route` in shadow/GA modules (AST/architecture test). |
| INV-GA1-04 | Fitness uses candidate pool fields only — no `CommitResult` input. |
| INV-GA1-05 | `observe_only` is always true in PR-GA-1 (config flag reserved for PR-GA-2 policy reuse). |
| INV-GA1-06 | Disabled config → no shadow step (or step with `enabled=false`, `candidate_count=0`). |

---

## §4 — PR-GA-1 contracts

### `GaEvolutionShadowConfig`

```python
@dataclass(frozen=True, slots=True)
class GaEvolutionShadowConfig:
    enabled: bool = False
    observe_only: bool = True  # PR-GA-1: must stay True
    population_size: int = 24
    generations: int = 8
    mutation_rate: float = 0.15
    tournament_size: int = 3
    elite_count: int = 2
    random_seed: int = 0
```

**Defaults:** `enabled=False` avoids surprise CI/runtime cost; ops/PR-GA-1b smoke sets `enabled=true`.

### `GaEvolutionShadowSummary` (metrics source)

| Field | Meaning |
|-------|---------|
| `enabled` | Config echo |
| `observe_only` | Always true in PR-GA-1 |
| `primary_commit_order` | Greedy genome `commit_order` |
| `shadow_proposed_commit_order` | Best GA genome `commit_order` |
| `shadow_fitness_total` | Best genome fitness |
| `generations_run` | Actual generations executed |
| `population_size` | Config echo |
| `overlap_violation_count` | Invalid genomes penalized (diagnostic) |
| `gene_count` | `len(shadow_proposed_commit_order)` |
| `anchor_count` | Distinct anchor coords in proposal |
| `order_agreement_ratio` | \|shared prefix ids\| / max(len primary, len shadow) |

### Genome validity (shadow GA)

A genome is **valid** iff:

```text
- Each candidate_id exists in normal pool
- No duplicate candidate_id
- Pairwise occupied_cells disjoint
- Pairwise fixed_output_transport cells disjoint (same rules as greedy _fot_conflict layout)
- len(commit_order) <= goal_count (same goal_count as greedy selection)
```

Invalid genomes receive fitness `-inf` (not committed).

### Fitness (PR-GA-1 v0)

Reuse greedy **base_score** semantics (no regret term) summed over genome order with simulated greedy occupancy walk:

```text
fitness(genome) =
  sum_{c in genome order} base_score(c | committed_occupied_so_far)
  - overlap_penalty * invalid_flag
```

`base_score` coefficients align with `SelectionConfig` defaults in `greedy_regret.py` (throughput_factor, rim alignment, probe_cost, fragmentation). **Do not** import commit-phase metrics.

### Pipeline step

```text
step_id: rttp.ga_evolution_shadow
phase: genome_fitness
event_type: rttp.ga_evolution_shadow
title: GA evolution shadow (observe-only)
passed: true when enabled and shadow run completed (even if proposal empty)
```

Insert **after** `RTTP_GENOME_SELECTION`, **before** deferred retry shadow / commit.

---

## §5 — PR-GA-2 scope (config-gated swap)

**Executable checklist:** [`../plans/2026-05-29-rttp-ga-evolution-pr-ga-2.md`](../plans/2026-05-29-rttp-ga-evolution-pr-ga-2.md) (implementation blocked until plan approval).

### In scope (separate PR / plan appendix)

- `SelectionMode` StrEnum: `greedy_regret` \| `evolution`
- `RttpPipelineConfig.selection_mode` default `greedy_regret`
- `select_genome_evolution(...)` — production path using same GA core as shadow (without shadow wrapper)
- `config_json.selection.mode` fail-closed mapper
- Tests: evolution mode returns genome; default unchanged on master fixtures
- Ops smoke: `--config-json-path` with `selection.mode=evolution` on `copy-import-495e552c`

### Non-goals (PR-GA-2)

- Changing candidate generator, route domain builder, or validation
- Removing greedy-regret (stays default)

---

## §6 — Module layout

```text
django_apps/asteroid_lab/contracts/ga_evolution_shadow.py
django_apps/asteroid_lab/optimization/selection/genome_fitness.py      # shared fitness
django_apps/asteroid_lab/optimization/selection/ga_evolution.py          # GA operators + select
django_apps/asteroid_lab/optimization/selection/ga_evolution_shadow.py   # shadow summary + metrics
django_apps/asteroid_lab/optimization/pipeline.py                        # step hook
django_apps/asteroid_lab/optimization/rttp_solver_summary.py             # step id
django_apps/asteroid_lab/replay/event_types.py                             # event_type const
django_apps/asteroid_lab/services/solver_runtime_entry.py                # config mapper
tests/unit/asteroid_lab/test_ga_evolution_shadow.py
tests/unit/architecture/test_ga_evolution_no_probe_route.py              # optional AST guard
```

---

## §7 — Testing strategy

### PR-GA-1

1. Unit: valid genome fitness > invalid overlapping genome
2. Unit: shadow disabled → `build_ga_evolution_shadow_summary` returns `enabled=false`, empty proposal
3. Unit: shadow enabled on toy pool → `shadow_proposed_commit_order` length ≤ goal_count
4. Integration-style: pipeline step recorded when enabled (mock sink or step list builder test)
5. Architecture: `ga_evolution*.py` must not import `probe_route` / routing probe modules
6. Regression: `pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map"` unchanged with default config

### PR-GA-2 (later)

- evolution mode selects genome; commit still passes on fixture
- default mode byte-equal greedy genome on frozen fixture

---

## §8 — Verification

**PR-GA-1 narrow:**

```powershell
python -m pytest tests/unit/asteroid_lab/test_ga_evolution_shadow.py -v --tb=short
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v --tb=short
python -m ruff check django_apps/asteroid_lab/contracts/ga_evolution_shadow.py django_apps/asteroid_lab/optimization/selection/genome_fitness.py django_apps/asteroid_lab/optimization/selection/ga_evolution.py django_apps/asteroid_lab/optimization/selection/ga_evolution_shadow.py
```

**Standing gates unchanged:** `test_capacity_sot.ps1`, `test_reconstruction_narrow.ps1`, `test_optimization_contamination.ps1`

---

## §9 — Governance

### `current_plan.md` (PR-GA-1 ACTIVE)

```text
ACTIVE: RTTP GA evolution PR-GA-1 — observe-only shadow
Spec: docs/superpowers/specs/2026-05-29-rttp-ga-evolution-design.md
Plan: docs/superpowers/plans/2026-05-29-rttp-ga-evolution.md
Blocks: PR-GA-2 (selection.mode swap) until PR-GA-1 CLOSED
```

### After PR-GA-1 CLOSED

```text
ACTIVE: RTTP GA evolution PR-GA-2 — config-gated selection.mode
```

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| GA runtime on large pools | Default `enabled=false`; bounded pop/gen; canon tests use toy pool |
| Fitness diverges from greedy | Shadow compares `order_agreement_ratio`; PR-GA-2 ops smoke |
| Duplicate scoring logic | `genome_fitness.py` shared by shadow + PR-GA-2 evolution |
| PR-B contamination | No replay imports; arch test for probe_route ban |

---

## Approval record

| Role | Decision | Date |
|------|----------|--------|
| RTTP GA Rollout Architect | B → A rollout approved | 2026-05-29 |
| PR-GA-1 | Shadow-first implementation authorized | 2026-05-29 |
