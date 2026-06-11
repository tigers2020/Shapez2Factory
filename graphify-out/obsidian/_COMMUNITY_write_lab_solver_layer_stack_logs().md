---
type: community
cohesion: 0.14
members: 20
---

# write_lab_solver_layer_stack_logs()

**Cohesion:** 0.14 - loosely connected
**Members:** 20 nodes

## Members
- [[Deprecated alias for ``build_layer04_inner_fill_post_summary_metrics``.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py
- [[Layer01ReconstructionOutput]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py
- [[Layer04RimPlacementResult]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_rim_bundle_placement/run.py
- [[Persist L1–L4 behavior + summary JSONL under var; return run log dir or None.]] - rationale - django_apps/asteroid_lab/services/solver_layer_stack_log.py
- [[Pure per-layer post-summary metric builders (Django-free core).]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py
- [[RimBundleCandidateSet]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py
- [[StackRunStatus]] - code - django_apps/asteroid_lab/services/solver_layer_stack_log.py
- [[Write per-layer JSONL logs for Lab solver runtime (observability only).]] - rationale - django_apps/asteroid_lab/services/solver_layer_stack_log.py
- [[build_layer01_post_summary_metrics()]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py
- [[build_layer02_post_summary_metrics()]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py
- [[build_layer03_post_summary_metrics()]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py
- [[build_layer03_rim_greedy_post_summary_metrics()]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py
- [[build_layer04_inner_fill_post_summary_metrics()]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py
- [[build_layer04_post_summary_metrics()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[build_layer05_post_summary_metrics()]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py
- [[build_layer06_post_summary_metrics()]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py
- [[post_summary_metrics.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py
- [[solver_layer_stack_log.py]] - code - django_apps/asteroid_lab/services/solver_layer_stack_log.py
- [[timed_ms()]] - code - django_apps/asteroid_lab/services/solver_layer_stack_log.py
- [[write_lab_solver_layer_stack_logs()]] - code - django_apps/asteroid_lab/services/solver_layer_stack_log.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/write_lab_solver_layer_stack_logs
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_run_layers_02_to_06()]]
- 3 edges to [[_COMMUNITY_ExteriorConnectionPlan]]
- 2 edges to [[_COMMUNITY_run_full_from_cleanup_recon()]]
- 2 edges to [[_COMMUNITY_layer_post_summary_log.py]]
- 2 edges to [[_COMMUNITY_build_solver_runtime_replay_frames()]]
- 2 edges to [[_COMMUNITY_layer03_rim_greedy_segment.py]]
- 1 edge to [[_COMMUNITY_build_reconstruction_complete_map()]]
- 1 edge to [[_COMMUNITY_run.py]]
- 1 edge to [[_COMMUNITY_.write_layer_post_summary()]]
- 1 edge to [[_COMMUNITY_generate_candidates()]]

## Top bridge nodes
- [[write_lab_solver_layer_stack_logs()]] - degree 15, connects to 4 communities
- [[RimBundleCandidateSet]] - degree 5, connects to 3 communities
- [[Layer01ReconstructionOutput]] - degree 4, connects to 2 communities
- [[Layer04RimPlacementResult]] - degree 4, connects to 2 communities
- [[build_layer02_post_summary_metrics()]] - degree 4, connects to 2 communities