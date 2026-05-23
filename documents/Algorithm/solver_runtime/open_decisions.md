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

êµ¬í˜„ v0?ì„œ ?•ì •?˜ì? ?Šì•˜ê±°ë‚˜ v1ë¡?ë¯¸ë£¬ ??ª©.

## OD-1: route_probe_start policy

**?„ì¬ ê³„ì•½:**

```text
fixed_output_transport = mandatory first belt/pipe cell
route_probe_start = next route search start
```

Route probe??`route_probe_start`?ì„œ ?œì‘?œë‹¤.

**?¥í›„ ê²€??**

```text
whether materialized route path should include fixed_output_transport automatically
```

**ê¶Œì¥ (v0):**

```text
yes, materialization should prepend fixed_output_transport before reservation path
```

??[`phase_k_route_materialization.md`](phase_k_route_materialization.md)

## OD-2: platform footprint + packing efficiency

v0 ê¶Œì¥:

```text
PLATFORM_FOOTPRINT_CELLS = 5   # gene pattern max footprint (not a game rule)
DEFAULT_MINEABLE_PACKING_EFFICIENCY = 0.75
estimated_extractor_groups = floor(mineable * packing_efficiency / 5)
```

`mineable / 5` ?¨ë…?€ ê±°ë?. ?©ëŸ‰ ì¶”ì •?€ **geometry ?´ë¦¬?¤í‹±**??ë¿?placement ë³´ì¥???„ë‹ˆ?? ??[`phase_c_capacity_route_goals.md`](phase_c_capacity_route_goals.md)

## OD-3: capacity enforcement level

**v0 (?„ë£Œ):**

```text
goal load penalty / edge sharing penalty
```

**v1 selector (2026-05-19, ?„ë£Œ):**

```text
hard trunk capacity in select_gene_candidates_greedy
skip overflow when alternate GoalLoadKey exists (trunk split)
fallback to penalty-only pool when all remaining would overflow
```

êµ¬í˜„: `would_exceed_trunk_capacity`, `trunk_platform_capacity` in `candidate_score.py`.

**2026-05-20 ?˜ì •:** trunk load??**platform count** (`assigned + 1 > capacity`). ?´ì „ `base_throughput` ?©ì‚°?€ ë¬¸ì„œ?€ ë¶ˆì¼ì¹˜í–ˆ?¼ë©°, Ã—16 bundle??goal??1ê°œë¡œë§?? íƒ?˜ëŠ” ?Œê? ?ì¸?´ì—ˆ??

**v1.1 (ë¯¸ì°©??:**

```text
commit-time reroute / trunk split in incremental commit
```

## OD-4: selector before GA

**ê²°ì • (Runtime v0):**

```text
A. capacity-aware greedy selector only ??Solver Button v0 ?•ë³¸
B. existing evolution engine ??v1 ?ëŠ” legacy reference only
```

**?´ìœ :**

```text
route/probe/commit correctness should stabilize before GA expands search complexity
```

??[`phase_i_candidate_selection.md`](phase_i_candidate_selection.md) Â· [`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) Â§3

## OD-5: route domain outer void padding

**v0 (?„ë£Œ):**

```text
OUTER_VOID_PADDING = 10  # fixed in input_contracts / reconstruction_adapter
MIN_GOAL_DISTANCE_FROM_MINEABLE = 3
MAX_GOAL_DISTANCE_FROM_MINEABLE = 5
asteroid_bbox vs route_domain_bbox split on OptimizationInput
```

**v1 (ë¯¸ì°©??:**

```text
solver config overrides for padding and goal distance band
ui_view_bbox separate from route_domain_bbox when replay viewport needs margin
```
