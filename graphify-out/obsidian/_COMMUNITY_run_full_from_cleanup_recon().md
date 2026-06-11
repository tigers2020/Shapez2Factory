---
type: community
cohesion: 0.42
members: 10
---

# run_full_from_cleanup_recon()

**Cohesion:** 0.42 - moderately connected
**Members:** 10 nodes

## Members
- [[Deprecated alias for ``run_layers_02_to_06`` (PR-3c layer renumber).]] - rationale - django_apps/asteroid_lab/layers/stack_runner.py
- [[Django wrapper over the pure core stack orchestrator (logssettingsfiles live h]] - rationale - django_apps/asteroid_lab/layers/stack_runner.py
- [[LayerBudgetContext]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_06_commit_validate/run.py
- [[LayerPostSummaryLogSession]] - code - django_apps/asteroid_lab/layers/stack_runner.py
- [[StackRunResult]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[_LayerStackRunner]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_solver_run.py
- [[run_full_from_cleanup_recon()]] - code - django_apps/asteroid_lab/layers/stack_runner.py
- [[run_layers_02_to_05()]] - code - django_apps/asteroid_lab/layers/stack_runner.py
- [[run_layers_02_to_06()]] - code - django_apps/asteroid_lab/layers/stack_runner.py
- [[stack_runner.py]] - code - django_apps/asteroid_lab/layers/stack_runner.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/run_full_from_cleanup_recon
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_.write_layer_post_summary()]]
- 2 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 2 edges to [[_COMMUNITY_run_layers_02_to_06()]]
- 2 edges to [[_COMMUNITY_ExteriorConnectionPlan]]
- 2 edges to [[_COMMUNITY_run_greedy_inner_fill()]]
- 2 edges to [[_COMMUNITY_write_lab_solver_layer_stack_logs()]]
- 1 edge to [[_COMMUNITY_try_load_default_space_transport_catalog]]
- 1 edge to [[_COMMUNITY_execute_layer_02_exterior_transport_plan]]
- 1 edge to [[_COMMUNITY_route_layer04_sequential()]]
- 1 edge to [[_COMMUNITY_run_layer_06_commit_validate()]]
- 1 edge to [[_COMMUNITY_deconstruct_snapshot()]]
- 1 edge to [[_COMMUNITY_record_existing_layout_inspection_frames]]
- 1 edge to [[_COMMUNITY_ReconstructionResult]]
- 1 edge to [[_COMMUNITY_layer_post_summary_log.py]]
- 1 edge to [[_COMMUNITY_build_reconstruction_complete_map()]]

## Top bridge nodes
- [[run_full_from_cleanup_recon()]] - degree 13, connects to 6 communities
- [[LayerBudgetContext]] - degree 12, connects to 6 communities
- [[run_layers_02_to_06()]] - degree 9, connects to 2 communities
- [[run_layers_02_to_05()]] - degree 8, connects to 1 community
- [[StackRunResult]] - degree 5, connects to 1 community