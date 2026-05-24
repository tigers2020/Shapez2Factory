# Phase 5 — Genome and Fitness


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_05_genome_fitness.md`](../../Algorithm/asteroid_lab_05_genome_fitness.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

> Fitness input contract·predictive vs observed separation — Algorithm [`asteroid_lab_05_genome_fitness.md`](../../Algorithm/asteroid_lab_05_genome_fitness.md) authority.

## Purpose

Define genome structure and fitness function to evaluate which bundle combinations to select from the candidate pool.

## Forbidden

Cell-level genome forbidden.

Bad structure:

```python
dict[Coord, CellState]
```

Recommended structure:

```python
tuple[CandidateId, ...]
```

## Scalability note

`Gene = candidate_id` alone may limit mutation space long-term. v1+ may reference `topology_signature`·routing preference on genome side. v0 assumes candidate ID combinations suffice.

## DTO

```python
@dataclass(frozen=True)
class Gene:
    candidate_id: str
    enabled: bool
    commit_order: int
```

`commit_order` is used for **confirmation·reorder sequence** within genome. Do not use field name `priority` to avoid clash with `RouteGoal.priority`.

```python
@dataclass(frozen=True)
class Genome:
    genome_id: str
    genes: tuple[Gene, ...]
    seed: int
```

```python
@dataclass(frozen=True)
class FitnessMetrics:
    selected_candidate_count: int
    extractor_count: int
    extension_count: int
    overlap_count: int
    unreachable_count: int
    total_route_cost: int
    max_trunk_sharing: int
    narrow_passage_occupied_count: int
```

`unreachable_count` is **not** count filtered from normal pool at candidate generation; it is count deemed unreachable when re-evaluating selected genes·candidates at **current fitness evaluation time** (or diagnostic rules).

```python
@dataclass(frozen=True)
class FitnessBreakdown:
    extractor_score: float
    extension_score: float
    throughput_score: float
    route_cost_penalty: float
    overlap_penalty: float
    unreachable_penalty: float
    congestion_penalty: float
    orphan_penalty: float
    corridor_block_penalty: float
    future_expansion_penalty: float
    narrow_passage_penalty: float
    trunk_sharing_penalty: float
    dead_end_penalty: float
    route_goal_quality_score: float
    route_goal_priority_penalty: float
    route_fragility_penalty: float
    shared_corridor_pressure_penalty: float
    total: float
    metrics: FitnessMetrics
```

`route_goal_quality_score` / `route_goal_priority_penalty` distinguish trunk attachment·soft corridor·margin·carve need **even when equally reachable**. Input uses `route_probe_result.reached_goal`·`goal_priority` stored on candidate.

`route_fragility_penalty` / `shared_corridor_pressure_penalty` are conservative items to reduce risk that **candidate-time reachable breaks at commit**. v0 may start **0 or simple heuristics** (e.g. how many shared corridor cells path crosses, narrow `RouteClass` segment length); **fields fixed in breakdown** to prevent implementation drift (see Phase 4 feasibility vs commitability).

### Why `unreachable_penalty` is needed

Phase 3 excludes unreachable from **normal pool**. Still keep `unreachable_penalty` in fitness because:

```text
1. diagnostic / experiment mode may reference abnormal candidates in genome
2. genome combination·commit sequence may become unreachable on re-eval when route_domain / reservation conflicts
3. stale probe snapshot defense (pre re-probe stage)
```

Keep this section so implementers do not remove penalty with “already filtered at candidate stage?”

## Fitness v0

Base formula (weights tunable):

```text
fitness =
    + extractor_count * 1000
    + extension_count * 250
    + throughput_score
    + route_goal_quality_score
    - route_cost * 5
    - route_goal_priority_penalty
    - overlap_count * 10000
    - unreachable_count * 20000
    - congestion_penalty
    - orphan_penalty
    - corridor_block_penalty
    - future_expansion_penalty
    - narrow_passage_penalty
    - trunk_sharing_penalty
    - dead_end_penalty
    - route_fragility_penalty
    - shared_corridor_pressure_penalty
```

### Route goal quality (qualitative)

Example weights tunable.

```text
existing_trunk connection: low priority penalty / high quality
soft_corridor: small penalty
external_margin: medium penalty
asteroid_carve required: high penalty (or unreachable-equivalent if carve_allowed False)
```

### Risk of flat scoring

If high-throughput candidates occupy narrow corridors entirely, **pass2 blockage·later unreachable** may recur.

Above penalty terms may start **0 or conservative heuristics** in v0, but **fields exposed in advance** to prevent drift.

Recommended dominance (qualitative):

```text
narrow_passage / corridor_block / future_expansion
> simple throughput gain (especially single-corridor collapse scenarios)
```

## Overlap handling

Two candidates using same occupied cell is conflict.

v0 allows conflict genomes with large penalty.

Remove in repair stage.

## Route Cost

Each candidate's cost read from **`route_probe_result.cost`** (Phase 3 snapshot).

Final commit stage must probe again.

## Invariant

```text
[ ] genome stores candidate ids, not cells
[ ] fitness must be deterministic for same input
[ ] overlap penalty dominates throughput gain
[ ] unreachable penalty dominates extractor gain
[ ] all score components exposed in breakdown (include in sum even if 0 in v0)
[ ] route_goal_quality_score·route_goal_priority_penalty deterministically linked to probe snapshot
[ ] FitnessMetrics preserves aggregate counts·sums (replay·debug)
```

## Tests

```text
test_genome_uses_candidate_ids
test_fitness_deterministic
test_fitness_penalizes_overlap
test_fitness_penalizes_unreachable
test_fitness_prefers_more_throughput_when_feasible
test_fitness_breakdown_total_matches_components
test_fitness_metrics_populated
test_fitness_route_goal_quality_prefers_trunk_over_margin_when_reachable_both
test_fitness_narrow_corridor_dominates_high_throughput_greed
```

## Completion criteria

```text
[ ] Gene/Genome DTO implemented
[ ] FitnessBreakdown + FitnessMetrics implemented
[ ] deterministic evaluator implemented
[ ] route_fragility_penalty·shared_corridor_pressure_penalty exist in breakdown (0 allowed in v0)
[ ] overlap/unreachable penalty tests pass
```
