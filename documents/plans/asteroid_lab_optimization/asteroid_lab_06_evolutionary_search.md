# Phase 6 — Evolutionary Search v0


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_06_evolutionary_search.md`](../../Algorithm/asteroid_lab_06_evolutionary_search.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

> **v0 pipeline:** GA not implemented — Algorithm [`asteroid_lab_06_evolutionary_search.md`](../../Algorithm/asteroid_lab_06_evolutionary_search.md) authority (banner·deterministic distant mutation).

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

`forced_distant_mutation_period`: **deterministic index within pool** (`evolution_distant_mutation_slot_index`); unseeded random **forbidden**. See Algorithm authority §Deterministic distant mutation.

**Builder validates** `population_size`·`elite_count`·`tournament_size` e.g. `population_size > 0`, `0 <= elite_count < population_size`.

`mutation_rate` must satisfy **`0.0 <= mutation_rate <= 1.0`**.

## Search target (responsibility boundary)

Evolutionary Search takes **candidate pool that already passed geometry·first-pass probe**.

```text
Responsible for combination (bundle id set) selection only
Forbidden: direct cell-level placement
Forbidden: direct belt·pipe path creation
Does not inherit rim traversal·candidate generation order as install order
```

Placement confirmation·path reservation performed by Phase 7 Incremental Commit per genome contract such as `Gene.commit_order`.

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

`convergence_reason`: **free strings forbidden**. Use enum above only.

## Mutation types

```text
add_candidate
remove_candidate
swap_candidate
replace_with_nearby_candidate
toggle_candidate
commit_order_shuffle
```

(Align with `Gene` `commit_order` field; deprecated name `priority_shuffle`.)

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

May leave **generation summaries** to observe convergence to same `topology_signature`·similar rim positions. Not used as algorithm input.

```python
@dataclass(frozen=True)
class GenomeDiversityMetrics:
    distinct_topology_signatures: int
    rim_cell_entropy_bits: float
    transport_kind_mix_score: float
```

Whether required field on `EvolutionResult` or only in replay `metrics` is implementation choice. v0 may **omit computation·fill 0**, but **DTO slot fixed** in docs.

## Termination conditions

Map termination to **`EvolutionConvergenceReason`** 1:1.

```text
max_generation -> MAX_GENERATION
max_stall_generation -> MAX_STALL_GENERATION
time_budget_ms -> TIME_BUDGET_MS
no_improvement -> NO_IMPROVEMENT
candidate_pool_exhausted -> CANDIDATE_POOL_EXHAUSTED
```

## Tie-break·determinism (required)

Beyond `same seed produces same result`, fix ranking at **equal fitness**.

```text
fitness tie-break (priority when same total):
1) FitnessBreakdown.total descending (higher preferred)
2) FitnessMetrics.selected_candidate_count descending (higher preferred; preserve throughput opportunity)
3) genome_id string ascending
```

Implementation fixes above as **single `sort_key` tuple** for `sorted(...)` / `heapq`.

## Invariant

```text
[ ] same seed produces same result (population init·mutation·tie-break included)
[ ] best fitness is non-decreasing under elitism (by total)
[ ] repair never creates unknown candidate id
[ ] mutation never generates cell-level genes
[ ] result includes convergence_reason (EvolutionConvergenceReason enum)
[ ] fitness tie-break key same in docs and implementation
[ ] commit_order kept as genome field; does not use rim·candidate pool enumeration order as commit authority (Phase 7)
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
[ ] EvolutionConfig DTO implemented
[ ] random initial population implemented
[ ] mutation-only search implemented
[ ] repair implemented
[ ] EvolutionConvergenceReason enum + EvolutionResult reflected
[ ] deterministic seed·tie-break tests pass
[ ] best genome returned
```
