---
type: community
cohesion: 0.20
members: 14
---

# .write_layer_post_summary()

**Cohesion:** 0.20 - loosely connected
**Members:** 14 nodes

## Members
- [[.close()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[.write_layer_post_summary()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[.write_stack_run_post_summary()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[LayerPostSummaryLogSession_1]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[LayerPostSummaryOutcome]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/layer_behavior_catalog.py
- [[LayerPostSummaryRecord]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[One stack run directory; one JSONL file per layer slug.]] - rationale - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[Per-layer behavior patterns and one-line summary formatters (observability only)]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/observability/layer_behavior_catalog.py
- [[_json_safe()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[emit_layer_post_summary()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[format_layer_summary_line()]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/layer_behavior_catalog.py
- [[layer_behavior_catalog.py]] - code - django_apps/asteroid_lab/layers/observability/layer_behavior_catalog.py
- [[layer_behavior_catalog.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/layer_behavior_catalog.py
- [[layer_behavior_for_slug()]] - code - src/shapez2_factory/application/asteroid_lab/layers/observability/layer_behavior_catalog.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/write_layer_post_summary
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_layer_post_summary_log.py]]
- 3 edges to [[_COMMUNITY_run_full_from_cleanup_recon()]]
- 2 edges to [[_COMMUNITY_run_layers_02_to_06()]]
- 1 edge to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_write_lab_solver_layer_stack_logs()]]

## Top bridge nodes
- [[emit_layer_post_summary()]] - degree 7, connects to 3 communities
- [[_json_safe()]] - degree 3, connects to 2 communities
- [[LayerPostSummaryLogSession_1]] - degree 7, connects to 1 community
- [[.write_layer_post_summary()]] - degree 7, connects to 1 community
- [[format_layer_summary_line()]] - degree 4, connects to 1 community