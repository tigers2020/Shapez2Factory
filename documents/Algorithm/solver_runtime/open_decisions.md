---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
related_docs:
  - documents/Algorithm/solver_runtime/phase_g_route_probe.md
  - documents/Algorithm/solver_runtime/phase_k_route_materialization.md
  - documents/Algorithm/solver_runtime/phase_i_candidate_selection.md
---

# Open Decisions (OD)

구현 v0에서 확정하지 않았거나 v1로 미룬 항목.

## OD-1: route_probe_start policy

**현재 계약:**

```text
fixed_output_transport = mandatory first belt/pipe cell
route_probe_start = next route search start
```

Route probe는 `route_probe_start`에서 시작한다.

**향후 검토:**

```text
whether materialized route path should include fixed_output_transport automatically
```

**권장 (v0):**

```text
yes, materialization should prepend fixed_output_transport before reservation path
```

→ [`phase_k_route_materialization.md`](phase_k_route_materialization.md)

## OD-2: platform footprint + packing efficiency

v0 권장:

```text
PLATFORM_FOOTPRINT_CELLS = 5   # gene pattern max footprint (not a game rule)
DEFAULT_MINEABLE_PACKING_EFFICIENCY = 0.75
estimated_extractor_groups = floor(mineable * packing_efficiency / 5)
```

`mineable / 5` 단독은 거부. 용량 추정은 **geometry 휴리스틱**일 뿐 placement 보장이 아니다. → [`phase_c_capacity_route_goals.md`](phase_c_capacity_route_goals.md)

## OD-3: capacity enforcement level

**v0 (완료):**

```text
goal load penalty / edge sharing penalty
```

**v1 selector (2026-05-19, 완료):**

```text
hard trunk capacity in select_gene_candidates_greedy
skip overflow when alternate GoalLoadKey exists (trunk split)
fallback to penalty-only pool when all remaining would overflow
```

구현: `would_exceed_trunk_capacity`, `trunk_platform_capacity` in `candidate_score.py`.

**v1.1 (미착수):**

```text
commit-time reroute / trunk split in incremental commit
```

## OD-4: selector before GA

**결정 (Runtime v0):**

```text
A. capacity-aware greedy selector only — Solver Button v0 정본
B. existing evolution engine — v1 또는 legacy reference only
```

**이유:**

```text
route/probe/commit correctness should stabilize before GA expands search complexity
```

→ [`phase_i_candidate_selection.md`](phase_i_candidate_selection.md) · [`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) §3

## OD-5: route domain outer void padding

**v0 (완료):**

```text
OUTER_VOID_PADDING = 10  # fixed in input_contracts / reconstruction_adapter
MIN_GOAL_DISTANCE_FROM_MINEABLE = 3
MAX_GOAL_DISTANCE_FROM_MINEABLE = 5
asteroid_bbox vs route_domain_bbox split on OptimizationInput
```

**v1 (미착수):**

```text
solver config overrides for padding and goal distance band
ui_view_bbox separate from route_domain_bbox when replay viewport needs margin
```
