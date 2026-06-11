---
type: community
cohesion: 0.19
members: 16
---

# build_failed_source_diagnostic()

**Cohesion:** 0.19 - loosely connected
**Members:** 16 nodes

## Members
- [[Build per-source L5 failure diagnostics at route commit failure sites.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/failed_source_diagnostics.py
- [[Layer 05 per-failed-source diagnostics (instrumentation only).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_failed_source_diagnostics.py
- [[Layer05FailedSourceDiagnostic]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_failed_source_diagnostics.py
- [[Layer05FailedSourceDiagnostic_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/failed_source_diagnostics.py
- [[Layer05FailureBucket]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_failed_source_diagnostics.py
- [[Layer05FailureReason]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/failed_source_diagnostics.py
- [[Layer05SourceView_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/failed_source_diagnostics.py
- [[_blocked_counts_from_detail()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/failed_source_diagnostics.py
- [[_nearest_goal_distance()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/failed_source_diagnostics.py
- [[aggregate_failure_histogram()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_failed_source_diagnostics.py
- [[aggregate_reason_histogram()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_failed_source_diagnostics.py
- [[build_failed_source_diagnostic()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/failed_source_diagnostics.py
- [[failed_source_diagnostics.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/failed_source_diagnostics.py
- [[failure_reason_to_bucket()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_failed_source_diagnostics.py
- [[format_l5_failure_eval_diagnostics()]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_failed_source_diagnostics.py
- [[layer05_failed_source_diagnostics.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_failed_source_diagnostics.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_failed_source_diagnostic
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_Coord]]
- 1 edge to [[_COMMUNITY_ExteriorConnectionPlan]]
- 1 edge to [[_COMMUNITY_ReplayEventType]]
- 1 edge to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_Enum]]
- 1 edge to [[_COMMUNITY_evaluate_against_golden()]]

## Top bridge nodes
- [[build_failed_source_diagnostic()]] - degree 9, connects to 2 communities
- [[format_l5_failure_eval_diagnostics()]] - degree 5, connects to 2 communities
- [[layer05_failed_source_diagnostics.py]] - degree 8, connects to 1 community
- [[_nearest_goal_distance()]] - degree 4, connects to 1 community
- [[Layer05FailureBucket]] - degree 3, connects to 1 community