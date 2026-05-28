# Phase 5 — Genome and Fitness

## Fitness input contract

| Role | Data source | Forbidden |
|------|-------------|------|
| **Predictive fitness** | candidate-phase `route_probe_result` + provisional `route_domain` | do not use commit re-probe results as fitness input |
| **Commit proof** | Phase 7 latest `RouteDomainSnapshotBuilder.build_snapshot` re-probe | fitness total is not a logical implication of commit success |

`route_fragility_penalty` / `shared_corridor_pressure_penalty` are **predictive estimates**. **Observed** `CommitSurvivabilityMetrics` are replay·post-commit only ([`asteroid_lab_10`](asteroid_lab_10_development_sequence.md) §10B) — **forbidden as solver/GA input**. `0.0` placeholder in replay `commit.survivability_summary` frame means **that frame does not own fitness breakdown**, not “no penalty”.

`PenaltyMode.CONSERVATIVE` minimum heuristic (implementation: `compute_conservative_fragility_penalties`):

```text
shared_corridor_pressure_penalty = α * |path_cells ∩ other_candidate_path_cells|
route_fragility_penalty = β * narrow_route_class_segment_count
```

`PenaltyMode.OFF` → both terms 0.

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

Long-term, `Gene = candidate_id` alone may leave mutation space insufficient. v1+ reviews referencing `topology_signature`·routing preference on genome side. v0 assumes candidate ID combinations suffice.

## DTO

```python
@dataclass(frozen=True)
class Gene:
    candidate_id: str
    enabled: bool
    commit_order: int
```

`commit_order` is used for **commit·reorder sequence** within genome. Do not use field name `priority` to avoid collision with `RouteGoal.priority`.

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

`unreachable_count` is not the count filtered from normal pool at candidate generation; it is the count deemed unreachable when re-evaluating selected genes·candidates at **current fitness evaluation time** (or per diagnostic rules).

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

`route_goal_quality_score` / `route_goal_priority_penalty` distinguish trunk attachment·soft corridor·margin·carve requirement **even when equally reachable**. Input uses `route_probe_result.reached_goal`·`goal_priority` stored on candidate.

`route_fragility_penalty` / `shared_corridor_pressure_penalty` are conservative terms to reduce risk that candidate-phase reachable breaks at commit. **0 only in `PenaltyMode.OFF`**; in `CONSERVATIVE` heuristics above may be non-zero. **Fields fixed in breakdown** (see Phase 4 feasibility vs commitability section).

### Why `unreachable_penalty` is needed

Phase 3 excludes unreachable candidates from **normal pool**. Reasons to keep `unreachable_penalty` in fitness:

```text
1. diagnostic / experiment mode may reference abnormal candidates in genome
2. genome combination·commit sequence later makes re-evaluation unreachable due to route_domain / reservation conflict
3. stale probe snapshot defense (pre re-probe stage)
```

Keep this section so implementers do not remove it asking “filtered at candidate stage, why penalty?”

## Fitness v0

Basic formula (weights tunable):

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

Example weights are tunable.

```text
existing_trunk connection: low priority penalty / high quality
soft_corridor: small penalty
external_margin: medium penalty
asteroid_carve required: high penalty (or treat like unreachable if carve_allowed False)
```

### Risk of flat scoring

If high-throughput candidates occupy all narrow corridors, **pass2 blockage·later unreachable** may recur.

Above penalty terms may start at **0 or conservative heuristic** in v0, but **expose fields early** to prevent implementation drift.

Recommended dominance (qualitative):

```text
narrow_passage / corridor_block / future_expansion
> simple throughput gain (especially single-corridor collapse scenarios)
```

## Overlap handling

Two candidates using the same occupied cell is conflict.

In v0, allow conflict genomes but apply large penalty.

Remove in repair stage.

## Route Cost

Each candidate's cost is read from **`route_probe_result.cost`** (Phase 3 snapshot).

Must probe again in final commit stage.

## Invariant

```text
[ ] genome stores candidate ids, not cells
[ ] fitness must be deterministic for same input
[ ] overlap penalty dominates throughput gain
[ ] unreachable penalty dominates extractor gain
[ ] all score components are exposed in breakdown (include in sum even if 0 in v0)
[ ] route_goal_quality_score·route_goal_priority_penalty linked deterministically to probe snapshot
[ ] FitnessMetrics preserves aggregate values such as counts·sums (replay·debug)
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
[ ] Gene/Genome DTO implementation
[ ] FitnessBreakdown + FitnessMetrics implementation
[ ] deterministic evaluator implementation
[ ] route_fragility_penalty·shared_corridor_pressure_penalty present in breakdown (0 allowed in v0)
[ ] overlap/unreachable penalty tests pass
```
