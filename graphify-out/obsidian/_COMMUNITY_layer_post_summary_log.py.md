---
type: community
cohesion: 0.38
members: 10
---

# layer_post_summary_log.py

**Cohesion:** 0.38 - loosely connected
**Members:** 10 nodes

## Members
- [[JSONL layer behavior + post-summary logs under var (flag-gated, max N runs reta]] - rationale - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[_log_root()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[_new_run_id()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[_prune_old_runs()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[_runs_parent()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[_safe_slug()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[_settings_bool()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[_settings_int()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[create_layer_post_summary_log_session()]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py
- [[layer_post_summary_log.py]] - code - django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/layer_post_summary_logpy
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_.write_layer_post_summary()]]
- 3 edges to [[_COMMUNITY_Path]]
- 2 edges to [[_COMMUNITY_write_lab_solver_layer_stack_logs()]]
- 1 edge to [[_COMMUNITY_run_full_from_cleanup_recon()]]
- 1 edge to [[_COMMUNITY_Enum]]

## Top bridge nodes
- [[layer_post_summary_log.py]] - degree 14, connects to 3 communities
- [[create_layer_post_summary_log_session()]] - degree 10, connects to 3 communities
- [[_runs_parent()]] - degree 5, connects to 1 community
- [[_safe_slug()]] - degree 4, connects to 1 community
- [[_log_root()]] - degree 3, connects to 1 community