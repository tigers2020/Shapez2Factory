---
type: community
cohesion: 0.09
members: 38
---

# entry_result_to_json_dict()

**Cohesion:** 0.09 - loosely connected
**Members:** 38 nodes

## Members
- [[._handle_logged()]] - code - django_apps/asteroid_lab/management/commands/run_solver.py
- [[._print_human_summary()]] - code - django_apps/asteroid_lab/management/commands/run_solver.py
- [[.add_arguments()_1]] - code - django_apps/asteroid_lab/management/commands/run_solver.py
- [[.handle()_1]] - code - django_apps/asteroid_lab/management/commands/run_solver.py
- [[Build lazy handle from persisted manifest summary (no composed frame list).]] - rationale - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[CLI entry for the solver runtime path used by HTTP run-solver.]] - rationale - django_apps/asteroid_lab/management/commands/run_solver.py
- [[Command_1]] - code - django_apps/asteroid_lab/management/commands/run_solver.py
- [[Lab replay lazy-load handle DTO (Sequence 13C transport contract).]] - rationale - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[LabReplayLazyHandle]] - code - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[LabReplayPayloadMode]] - code - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[Prefer the latest frame that still shows equipment; fall back to the last slot.]] - rationale - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[Return a single-token value for BA-9 access-log fields.]] - rationale - django_apps/asteroid_lab/management/commands/run_solver.py
- [[Run the solver through the pure CLI subprocess path only.]] - rationale - django_apps/asteroid_lab/services/solver_runtime_entry.py
- [[SolverRuntimeEntryResult]] - code - django_apps/asteroid_lab/services/solver_runtime_entry.py
- [[SolverSubprocessRequest]] - code - django_apps/asteroid_lab/services/solver_runtime_entry.py
- [[Subprocess-only solver runtime entry for Django artifactviewer orchestration.]] - rationale - django_apps/asteroid_lab/services/solver_runtime_entry.py
- [[True when a timeline frame still carries equipment sprites (not terrain-only).]] - rationale - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[_build_subprocess_request()]] - code - django_apps/asteroid_lab/services/solver_runtime_entry.py
- [[_console_token()]] - code - django_apps/asteroid_lab/management/commands/run_solver.py
- [[_empty_replay_track_metrics()]] - code - django_apps/asteroid_lab/services/solver_runtime_entry.py
- [[_lab_replay_fetch_url()]] - code - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[_latest_map_input()]] - code - django_apps/asteroid_lab/services/solver_runtime_entry.py
- [[_map_view_cell_rows()]] - code - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[_normalize_milestone_track_metrics()]] - code - django_apps/asteroid_lab/services/solver_runtime_entry.py
- [[_replay_payload_version_from_summary()]] - code - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[_run_subprocess_runtime_for_project()]] - code - django_apps/asteroid_lab/services/solver_runtime_entry.py
- [[build_lab_replay_lazy_handle()]] - code - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[build_lab_replay_lazy_handle_from_summary()]] - code - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[empty_milestone_track_metrics()]] - code - django_apps/asteroid_lab/services/solver_runtime_types.py
- [[entry_result_to_json_dict()]] - code - django_apps/asteroid_lab/services/solver_runtime_entry.py
- [[frame_has_sprite_layout_cells()]] - code - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[lab_replay_lazy_handle.py]] - code - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[lab_replay_manifest_json_dict()]] - code - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[lab_replay_payload_mode()]] - code - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[preview_frame_index_for_lab_replay()]] - code - django_apps/asteroid_lab/services/lab_replay_lazy_handle.py
- [[run_solver.py]] - code - django_apps/asteroid_lab/management/commands/run_solver.py
- [[run_solver_runtime_for_project()]] - code - django_apps/asteroid_lab/services/solver_runtime_entry.py
- [[solver_runtime_entry.py]] - code - django_apps/asteroid_lab/services/solver_runtime_entry.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/entry_result_to_json_dict
SORT file.name ASC
```

## Connections to other communities
- 20 edges to [[_COMMUNITY_Any]]
- 7 edges to [[_COMMUNITY_lab_page_context()]]
- 4 edges to [[_COMMUNITY_SolverRun]]
- 3 edges to [[_COMMUNITY_AsteroidMapInput]]
- 2 edges to [[_COMMUNITY_run_solver_subprocess()]]
- 2 edges to [[_COMMUNITY__run_solver_post_traced()]]
- 1 edge to [[_COMMUNITY_Path]]
- 1 edge to [[_COMMUNITY_BaseCommand]]
- 1 edge to [[_COMMUNITY__run_artifact()]]
- 1 edge to [[_COMMUNITY_build_game_data_snapshot_payload()]]
- 1 edge to [[_COMMUNITY_ingest_artifact_for_project()]]
- 1 edge to [[_COMMUNITY_GeneTemplate]]
- 1 edge to [[_COMMUNITY_solver_runtime_types.py]]

## Top bridge nodes
- [[_run_subprocess_runtime_for_project()]] - degree 12, connects to 5 communities
- [[_build_subprocess_request()]] - degree 8, connects to 5 communities
- [[entry_result_to_json_dict()]] - degree 13, connects to 3 communities
- [[run_solver_runtime_for_project()]] - degree 9, connects to 2 communities
- [[._handle_logged()]] - degree 8, connects to 2 communities