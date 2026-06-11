---
type: community
cohesion: 0.09
members: 27
---

# _run_solver_post_traced()

**Cohesion:** 0.09 - loosely connected
**Members:** 27 nodes

## Members
- [[Console trace for Django-side Asteroid Lab solver invocations.]] - rationale - django_apps/asteroid_lab/observability/cli_invoke_trace.py
- [[Emit BA-9 startend lines for a Django solver invocation.]] - rationale - django_apps/asteroid_lab/observability/cli_invoke_trace.py
- [[JSON manifest of baked atomic part PNGs (for recipe graph tile Canvas2D composit]] - rationale - django_apps/web/views/staff_shared.py
- [[JsonResponse]] - code - django_apps/web/views/staff_shared.py
- [[POST JSON resolve one cell at world (x, y) for a persisted class`ReplayFrame`]] - rationale - django_apps/web/views/public_pages.py
- [[POST run solver runtime pipeline for one project; JSON response (PR8 entry).]] - rationale - django_apps/web/views/public_pages.py
- [[Parse optional JSON POST body into runtime ``config`` (PR-K).]] - rationale - django_apps/web/views/public_pages.py
- [[Require login at ``settings.LOGIN_URL`` and ``is_staff`` (403 if logged-in but n]] - rationale - django_apps/web/views/staff_shared.py
- [[Return a single-token value for access-log fields.]] - rationale - django_apps/asteroid_lab/observability/cli_invoke_trace.py
- [[Staff-only helpers shared by non-macro staff endpoints.]] - rationale - django_apps/web/views/staff_shared.py
- [[Warm one graph-preview PNG (staff-only; validates cache_key against preview_scen]] - rationale - django_apps/web/views/staff_shared.py
- [[_console_token()_1]] - code - django_apps/asteroid_lab/observability/cli_invoke_trace.py
- [[_parse_graph_preview_warm_body()]] - code - django_apps/web/views/staff_shared.py
- [[_run_solver_post_traced()]] - code - django_apps/web/views/public_pages.py
- [[_run_solver_request_config()]] - code - django_apps/web/views/public_pages.py
- [[_solver_async_enabled()]] - code - django_apps/web/views/public_pages.py
- [[asteroid_miner_layout_project_run_solver()]] - code - django_apps/web/views/public_pages.py
- [[asteroid_miner_layout_replay_frame_cell()]] - code - django_apps/web/views/public_pages.py
- [[cli_invoke_trace()]] - code - django_apps/asteroid_lab/observability/cli_invoke_trace.py
- [[cli_invoke_trace.py]] - code - django_apps/asteroid_lab/observability/cli_invoke_trace.py
- [[health()]] - code - django_apps/shapez_core/views.py
- [[macro_pattern_staff_api_graph_preview_warm()]] - code - django_apps/web/views/staff_shared.py
- [[shape_part_sprite_manifest()]] - code - django_apps/web/views/staff_shared.py
- [[shape_preview()]] - code - django_apps/shapez_core/views.py
- [[staff_shared.py]] - code - django_apps/web/views/staff_shared.py
- [[staff_site_required()]] - code - django_apps/web/views/staff_shared.py
- [[views.py_1]] - code - django_apps/shapez_core/views.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/_run_solver_post_traced
SORT file.name ASC
```

## Connections to other communities
- 10 edges to [[_COMMUNITY_HttpRequest]]
- 7 edges to [[_COMMUNITY_public_pages.py]]
- 4 edges to [[_COMMUNITY_Any]]
- 4 edges to [[_COMMUNITY_lab_page_context()]]
- 2 edges to [[_COMMUNITY_entry_result_to_json_dict()]]
- 1 edge to [[_COMMUNITY__run_artifact()]]
- 1 edge to [[_COMMUNITY_AsteroidMapInput]]
- 1 edge to [[_COMMUNITY_SolverRun]]
- 1 edge to [[_COMMUNITY_build_game_data_snapshot_payload()]]
- 1 edge to [[_COMMUNITY_build_demo_parse_row()]]
- 1 edge to [[_COMMUNITY_build_asteroid_game_data_snapshot_with_p]]
- 1 edge to [[_COMMUNITY_replay_service.py]]
- 1 edge to [[_COMMUNITY_graph_preview.py]]
- 1 edge to [[_COMMUNITY_replay_frame_cell_lookup.py]]
- 1 edge to [[_COMMUNITY_game_data_snapshot_provenance.py]]

## Top bridge nodes
- [[_run_solver_post_traced()]] - degree 16, connects to 10 communities
- [[asteroid_miner_layout_replay_frame_cell()]] - degree 6, connects to 4 communities
- [[asteroid_miner_layout_project_run_solver()]] - degree 7, connects to 3 communities
- [[_run_solver_request_config()]] - degree 6, connects to 3 communities
- [[JsonResponse]] - degree 12, connects to 2 communities