---
type: community
cohesion: 0.07
members: 51
---

# lab_page_context()

**Cohesion:** 0.07 - loosely connected
**Members:** 51 nodes

## Members
- [[Artifact-first lab replay cache readers for ``SolverRun`` UIindex fields.]] - rationale - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[Attach scalar metadata to the active request trace (no-op when disabled).]] - rationale - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[Cheap aggregate for perf records (not used by solver or replay logic).]] - rationale - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[Collect phase timings for one HTTP handler; emit one JSONL line on exit.]] - rationale - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[Default template context for the asteroid mining lab page (no demo payload).]] - rationale - django_apps/web/services/asteroid_lab_page_context.py
- [[Feature-flagged JSONL latency traces for Asteroid Lab HTTP paths (output-only).]] - rationale - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[Fresh read-merge-write; preserve unrelated ``config_json`` keys (§4.8).]] - rationale - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[Lab run summary uses string ``id`` (see ``lab_run_summary_from_solver_summary``)]] - rationale - django_apps/web/services/asteroid_lab_page_context.py
- [[Lab shell context. Product replay is one composed timeline per project.]] - rationale - django_apps/web/services/asteroid_lab_page_context.py
- [[Load manifest summary from artifactindex fields before legacy config fallback.]] - rationale - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[Load replay frames artifact-first, then dedicated DB cache, then legacy config.]] - rationale - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[One SSR cell when server replay exists; Lab JS rebuilds the real grid.]] - rationale - django_apps/web/services/asteroid_lab_page_context.py
- [[Read-only DB summary of miner seed patterns (display only, never solver input).]] - rationale - django_apps/web/services/asteroid_lab_page_context.py
- [[Record a pre-measured phase duration in milliseconds.]] - rationale - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[Return artifact index summary to preserve across composed-cache writes.]] - rationale - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[Time one phase when a ``lab_perf_trace_request`` context is active.]] - rationale - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[True when ``replay_core.jsonl`` is indexed (compose source, not display cache).]] - rationale - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[True when cached L3 complete used replay_core only (no committed overlays).]] - rationale - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[UTF-8 size of ``value`` as compact JSON (perf meta only; not solver input).]] - rationale - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[Whether composed replay may be readwritten on ``SolverRun`` (not solver CLI inp]] - rationale - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[_Collector]] - code - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[_artifact_replay_source_snapshot()]] - code - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[_dict_or_none()]] - code - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[_gene_template_catalog()]] - code - django_apps/web/services/asteroid_lab_page_context.py
- [[_is_stale_thin_artifact_l3_cache()]] - code - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[_neutral_overlay_matrix()]] - code - django_apps/web/services/asteroid_lab_page_context.py
- [[_repo_base_dir()_1]] - code - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[_single_cell_overlay_matrix()]] - code - django_apps/web/services/asteroid_lab_page_context.py
- [[_solver_run_id_from_lab_summary()]] - code - django_apps/web/services/asteroid_lab_page_context.py
- [[asteroid_lab_page_context.py]] - code - django_apps/web/services/asteroid_lab_page_context.py
- [[asteroid_miner_layout_project_solver_run_lab_replay()]] - code - django_apps/web/views/public_pages.py
- [[build_manifest_summary_from_compose()]] - code - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[count_full_map_cells()]] - code - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[emit_lab_perf_trace()]] - code - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[is_artifact_replay_source_summary()]] - code - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[is_cache_summary_valid()]] - code - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[lab_page_context()]] - code - django_apps/web/services/asteroid_lab_page_context.py
- [[lab_perf_trace.py]] - code - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[lab_perf_trace_enabled()]] - code - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[lab_perf_trace_log_path()]] - code - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[lab_perf_trace_request()]] - code - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[lab_replay_persisted_cache.py]] - code - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[load_composed_frames_for_run_id()]] - code - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[load_manifest_summary_for_run_id()]] - code - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[neutral_lab_context()]] - code - django_apps/web/services/asteroid_lab_page_context.py
- [[perf_span()]] - code - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[persist_composed_replay_for_run_id()]] - code - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[record_perf_meta()]] - code - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[record_perf_ms()]] - code - django_apps/asteroid_lab/observability/lab_perf_trace.py
- [[replay_compose_cache_enabled()]] - code - django_apps/asteroid_lab/services/lab_replay_persisted_cache.py
- [[serialized_json_utf8_bytes()]] - code - django_apps/asteroid_lab/observability/lab_perf_trace.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/lab_page_context
SORT file.name ASC
```

## Connections to other communities
- 18 edges to [[_COMMUNITY_Any]]
- 7 edges to [[_COMMUNITY_entry_result_to_json_dict()]]
- 5 edges to [[_COMMUNITY_public_pages.py]]
- 5 edges to [[_COMMUNITY_build_solver_runtime_replay_frames_from_]]
- 5 edges to [[_COMMUNITY_build_lab_replay_frames_for_project()]]
- 4 edges to [[_COMMUNITY__run_solver_post_traced()]]
- 2 edges to [[_COMMUNITY_Path]]
- 2 edges to [[_COMMUNITY_ingest_artifact_for_project()]]
- 1 edge to [[_COMMUNITY_create_solver_run()]]
- 1 edge to [[_COMMUNITY_HttpRequest]]
- 1 edge to [[_COMMUNITY_replay_service.py]]

## Top bridge nodes
- [[lab_page_context()]] - degree 21, connects to 5 communities
- [[asteroid_miner_layout_project_solver_run_lab_replay()]] - degree 15, connects to 5 communities
- [[perf_span()]] - degree 9, connects to 4 communities
- [[load_composed_frames_for_run_id()]] - degree 11, connects to 3 communities
- [[persist_composed_replay_for_run_id()]] - degree 11, connects to 3 communities