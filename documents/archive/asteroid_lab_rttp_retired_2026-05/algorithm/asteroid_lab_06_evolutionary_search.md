# Phase 6 — Evolutionary Search v0

> **v0 pipeline (2026-05-21):** Current runtime is **candidate select + incremental commit** only. GA loop·`FitnessEvaluator` are **unimplemented** (`replay_event_coverage.DEFERRED_NO_EVOLUTION_V0`). This document is the **DTO·algorithm contract** canonical source.

## Purpose

Optimize bundle candidate combinations via evolutionary search.

## v0 strategy

Initial version favors mutation + repair + elitism over complex crossover.

```text
initial population
→ evaluate
→ select elites
→ mutate
→ repair
→ evaluate
→ repeat
```

## Input

```python
CandidatePool
FitnessEvaluator
EvolutionConfig
```

### `EvolutionConfig`

```python
@dataclass(frozen=True)
class EvolutionConfig:
    seed: int
    population_size: int
    elite_count: int
    mutation_rate: float
    tournament_size: int
    max_generation: int
    max_stall_generation: int
    time_budget_ms: int | None
    forced_distant_mutation_period: int | None
```

When `forced_distant_mutation_period` is `N`, **every N generations** force at least one **distant candidate replacement** (e.g. rim extreme swap, **deterministic index selection within pool**) that is not `replace_with_nearby_candidate`, by **deterministic rule**. `None` disables. **Forbidden:** unseeded randomness such as `random`·`time`·`uuid4`.

## Deterministic distant mutation

```python
slot_index = evolution_distant_mutation_slot_index(
    seed=config.seed,
    generation=generation,
    genome_id=genome.genome_id,
    population_size=config.population_size,
)
# rim extreme swap: ordered candidate_ids[slot_index], candidate_ids[(slot_index + 1) % pool_size]
```

`same seed` + same `generation`·`genome_id` → same `slot_index` → same replacement target. Implementation: [`fitness_contracts.py`](django_apps/asteroid_lab/optimization/fitness_contracts.py).

`population_size`·`elite_count`·`tournament_size` are **validated in builder** with constraints such as `population_size > 0`, `0 <= elite_count < population_size`.

`mutation_rate` must satisfy **`0.0 <= mutation_rate <= 1.0`**.

## Search target (responsibility boundary)

Evolutionary Search takes as input a **candidate pool that already passed geometry·first-pass probe**.

```text
responsible only for combination (bundle id set) selection
forbidden: direct cell-level placement
forbidden: direct belt·pipe path generation
does not inherit rim traversal order·candidate generation order as installation order
```

Placement commit·path reservation is performed by Phase 7 Incremental Commit per genome contract such as `Gene.commit_order`.

## Output

```python
class EvolutionConvergenceReason(Enum):
    MAX_GENERATION = "max_generation"
    MAX_STALL_GENERATION = "max_stall_generation"
    TIME_BUDGET_MS = "time_budget_ms"
    NO_IMPROVEMENT = "no_improvement"
    CANDIDATE_POOL_EXHAUSTED = "candidate_pool_exhausted"
```

```python
@dataclass(frozen=True)
class EvolutionResult:
    best_genome: Genome
    best_fitness: FitnessBreakdown
    generation_count: int
    evaluated_genome_count: int
    convergence_reason: EvolutionConvergenceReason
```

`convergence_reason`: **no free strings**. Use enum above only.

## Mutation types

```text
add_candidate
remove_candidate
swap_candidate
replace_with_nearby_candidate
toggle_candidate
commit_order_shuffle
```

(Align with `Gene.commit_order` field; deprecated name `priority_shuffle`.)

## Repair types

```text
remove_overlap_low_score
remove_unreachable
remove_corridor_blocker
dedupe_candidate
limit_bundle_count
```

## Selection

v0 recommendation:

```text
elitism + tournament selection
```

## Population diversity (log·replay metrics)

Generation summaries may be retained to observe convergence to same `topology_signature`·similar rim positions. Not used as algorithm input.

```python
@dataclass(frozen=True)
class GenomeDiversityMetrics:
    distinct_topology_signatures: int
    rim_cell_entropy_bits: float
    transport_kind_mix_score: float
```

Whether to require as field on `EvolutionResult` or only in replay `metrics` is implementation choice. v0 allows **skip computation·fill 0**, but **DTO slot** is fixed in docs.

## Termination conditions

Termination maps 1:1 to **`EvolutionConvergenceReason`**.

```text
max_generation -> MAX_GENERATION
max_stall_generation -> MAX_STALL_GENERATION
time_budget_ms -> TIME_BUDGET_MS
no_improvement -> NO_IMPROVEMENT
candidate_pool_exhausted -> CANDIDATE_POOL_EXHAUSTED
```

## Tie·determinism (required)

Beyond `same seed produces same result`, fix ranking at **equal fitness**.

```text
fitness tie-break (priority when same total):
1) FitnessBreakdown.total descending (higher preferred)
2) FitnessMetrics.selected_candidate_count descending (higher preferred; preserve throughput opportunity)
3) genome_id string ascending
```

Implementation fixes above keys as **single `sort_key` tuple** for `sorted(...)` / `heapq`.

## Invariant

```text
[ ] same seed produces same result (includes population init·mutation·tie-break)
[ ] best fitness is non-decreasing under elitism (by total)
[ ] repair never creates unknown candidate id
[ ] mutation never generates cell-level genes
[ ] result includes convergence_reason (EvolutionConvergenceReason enum)
[ ] fitness tie-break keys identical in docs and implementation
[ ] commit_order kept as genome field; rim·candidate pool enumeration order not used as commit canonical (Phase 7)
```

## Tests

```text
test_evolution_same_seed_deterministic
test_evolution_best_fitness_non_decreasing_with_elitism
test_evolution_repair_removes_overlap
test_evolution_mutation_keeps_valid_candidate_ids
test_evolution_result_has_convergence_reason_enum
test_evolution_fitness_tie_break_deterministic
```

## Completion criteria

```text
[ ] EvolutionConfig DTO implementation
[ ] random initial population implementation
[ ] mutation-only search implementation
[ ] repair implementation
[ ] EvolutionConvergenceReason enum + EvolutionResult reflected
[ ] deterministic seed·tie-break tests pass
[ ] return best genome
```
