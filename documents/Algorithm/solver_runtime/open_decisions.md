---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
related_docs:
  - documents/Algorithm/solver_runtime/phase_g_route_probe.md
  - documents/Algorithm/solver_runtime/phase_k_route_materialization.md
  - documents/Algorithm/solver_runtime/phase_i_candidate_selection.md
---

# Open Decisions (OD)

Items not finalized in v0 implementation or deferred to v1.

## OD-1: route_probe_start policy

**Current contract:**

```text
fixed_output_transport = mandatory first belt/pipe cell
route_probe_start = next route search start
```

Route probe starts from `route_probe_start`.

**Future review:**

```text
whether materialized route path should include fixed_output_transport automatically
```

**Recommendation (v0):**

```text
yes, materialization should prepend fixed_output_transport before reservation path
```

See [`phase_k_route_materialization.md`](phase_k_route_materialization.md)

## OD-2: platform footprint + packing efficiency

v0 recommendation:

```text
PLATFORM_FOOTPRINT_CELLS = 5   # gene pattern max footprint (not a game rule)
DEFAULT_MINEABLE_PACKING_EFFICIENCY = 0.75
estimated_extractor_groups = floor(mineable * packing_efficiency / 5)
```

`mineable / 5` alone is coarse. Capacity estimation is **geometry heuristic** only; placement guarantee is separate. See [`phase_c_capacity_route_goals.md`](phase_c_capacity_route_goals.md)

## OD-3: capacity enforcement level

**v0 (complete):**

```text
goal load penalty / edge sharing penalty
```

**v1 selector (2026-05-19, complete):**

```text
hard trunk capacity in select_gene_candidates_greedy
skip overflow when alternate GoalLoadKey exists (trunk split)
fallback to penalty-only pool when all remaining would overflow
```

Implementation: `would_exceed_trunk_capacity`, `trunk_platform_capacity` in `candidate_score.py`.

**2026-05-20 correction:** trunk load is **platform count** (`assigned + 1 > capacity`). Previous `base_throughput` multiplication was inconsistent with docs; ×16 bundle counted as 1 platform per goal was the bug.

**v1.1 (not adopted):**

```text
commit-time reroute / trunk split in incremental commit
```

## OD-4: selector before GA

**Decision (Runtime v0):**

```text
A. capacity-aware greedy selector only ? Solver Button v0 canonical
B. existing evolution engine ? v1 or legacy reference only
```

**Rationale:**

```text
route/probe/commit correctness should stabilize before GA expands search complexity
```

See [`phase_i_candidate_selection.md`](phase_i_candidate_selection.md) · [`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) §3

## OD-5: route domain outer void padding

**v0 (complete):**

```text
OUTER_VOID_PADDING = 10  # fixed in input_contracts / reconstruction_adapter
MIN_GOAL_DISTANCE_FROM_MINEABLE = 3
MAX_GOAL_DISTANCE_FROM_MINEABLE = 5
asteroid_bbox vs route_domain_bbox split on OptimizationInput
```

**v1 (not adopted):**

```text
solver config overrides for padding and goal distance band
ui_view_bbox separate from route_domain_bbox when replay viewport needs margin
```
