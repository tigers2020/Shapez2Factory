---
type: community
cohesion: 0.25
members: 14
---

# build_initial_replay_for_map_input()

**Cohesion:** 0.25 - loosely connected
**Members:** 14 nodes

## Members
- [[A6.2 — Wire copy import to decode + inspection replay frames (UI-only artifacts)]] - rationale - django_apps/asteroid_lab/services/replay_pipeline_service.py
- [[Decode copy text, persist JSON, scaffold SolverRunReplayTrack, record inspectio]] - rationale - django_apps/asteroid_lab/services/replay_pipeline_service.py
- [[Drop runtime solver artifacts; rebuild inspection replay (map clean through reco]] - rationale - django_apps/asteroid_lab/services/lab_map_reset_service.py
- [[InitialReplayPipelineResultDTO]] - code - django_apps/asteroid_lab/services/replay_pipeline_service.py
- [[Reset Lab project map to inspection-only DB state (decode + cleanupreconstructi]] - rationale - django_apps/asteroid_lab/services/lab_map_reset_service.py
- [[_default_run_key()]] - code - django_apps/asteroid_lab/services/replay_pipeline_service.py
- [[_inspection_run_key_for_map_input()]] - code - django_apps/asteroid_lab/services/lab_map_reset_service.py
- [[_latest_cell_snapshot_pk()]] - code - django_apps/asteroid_lab/services/replay_pipeline_service.py
- [[_latest_reconstructed_map_pk()]] - code - django_apps/asteroid_lab/services/replay_pipeline_service.py
- [[_result_from_completed_track()]] - code - django_apps/asteroid_lab/services/replay_pipeline_service.py
- [[build_initial_replay_for_map_input()]] - code - django_apps/asteroid_lab/services/replay_pipeline_service.py
- [[lab_map_reset_service.py]] - code - django_apps/asteroid_lab/services/lab_map_reset_service.py
- [[replay_pipeline_service.py]] - code - django_apps/asteroid_lab/services/replay_pipeline_service.py
- [[reset_project_map_to_inspection_clean()]] - code - django_apps/asteroid_lab/services/lab_map_reset_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_initial_replay_for_map_input
SORT file.name ASC
```

## Connections to other communities
- 6 edges to [[_COMMUNITY_record_existing_layout_inspection_frames]]
- 5 edges to [[_COMMUNITY_AsteroidMapInput]]
- 1 edge to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_SolverRun]]
- 1 edge to [[_COMMUNITY_create_solver_run()]]
- 1 edge to [[_COMMUNITY_Enum]]
- 1 edge to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_public_pages.py]]
- 1 edge to [[_COMMUNITY_build_lab_replay_frames_for_project()]]
- 1 edge to [[_COMMUNITY_build_reconstructed_map_persist_payload(]]
- 1 edge to [[_COMMUNITY_decode_copy_string()]]
- 1 edge to [[_COMMUNITY_normalize_decoded_blueprint()]]
- 1 edge to [[_COMMUNITY_asteroid_miner_layout_create_project()]]

## Top bridge nodes
- [[build_initial_replay_for_map_input()]] - degree 22, connects to 8 communities
- [[_result_from_completed_track()]] - degree 8, connects to 3 communities
- [[lab_map_reset_service.py]] - degree 5, connects to 2 communities
- [[reset_project_map_to_inspection_clean()]] - degree 6, connects to 1 community
- [[_inspection_run_key_for_map_input()]] - degree 5, connects to 1 community