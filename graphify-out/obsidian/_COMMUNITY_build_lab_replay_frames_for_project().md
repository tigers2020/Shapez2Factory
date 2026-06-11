---
type: community
cohesion: 0.15
members: 22
---

# build_lab_replay_frames_for_project()

**Cohesion:** 0.15 - loosely connected
**Members:** 22 nodes

## Members
- [[Compose Lab + solver runtime replay into product timeline JSON (never mutates so]] - rationale - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[Island-local replay projection (PR-F Wave C; no dense server params).]] - rationale - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[Latest class`ReplayTrack` that has at least one frame (display-only read).]] - rationale - django_apps/web/services/asteroid_lab_page_context.py
- [[Latest replay track (with frames) for one project (display-only).]] - rationale - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[Load persisted solver runtime replay frames from latest SolverRun.config_json.]] - rationale - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[Read-only product replay timeline for Lab page (Lab ORM + solver runtime frames)]] - rationale - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[ReplayProjectionContext_1]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[ReplayTrack_1]] - code - django_apps/web/services/asteroid_lab_page_context.py
- [[_empty_track_metrics()]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[_frame_row_from_model()]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[_lab_replay_diagnostic_reason()]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[_lab_timeline_frames_for_project()]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[_lab_timeline_frames_from_track()]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[_latest_inspection_replay_track()]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[_solver_runtime_timeline_frames_for_project()]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[_solver_runtime_timeline_frames_for_run()]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[_track_metrics_from_serialized_frames()]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[build_lab_replay_frames_for_project()]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[get_latest_lab_replay_track()]] - code - django_apps/web/services/asteroid_lab_page_context.py
- [[get_latest_lab_replay_track_for_project()]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[lab_replay_timeline_payload.py]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
- [[resolve_replay_projection_context_for_project()]] - code - django_apps/asteroid_lab/services/lab_replay_timeline_payload.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_lab_replay_frames_for_project
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_timeline_serialization.py]]
- 5 edges to [[_COMMUNITY_Any]]
- 5 edges to [[_COMMUNITY_lab_page_context()]]
- 2 edges to [[_COMMUNITY_replay_service.py]]
- 2 edges to [[_COMMUNITY_build_layer02_timeline_frame_wire_dict()]]
- 2 edges to [[_COMMUNITY_flowbite.min.js]]
- 2 edges to [[_COMMUNITY_enrich_lab_timeline_frames_with_terrain_]]
- 1 edge to [[_COMMUNITY_lab_timeline_adapter.py]]
- 1 edge to [[_COMMUNITY_compose_replay_timeline()]]
- 1 edge to [[_COMMUNITY_ingest_artifact_for_project()]]
- 1 edge to [[_COMMUNITY_build_solver_runtime_replay_frames_from_]]
- 1 edge to [[_COMMUNITY_SolverRun]]
- 1 edge to [[_COMMUNITY_build_initial_replay_for_map_input()]]
- 1 edge to [[_COMMUNITY_public_pages.py]]

## Top bridge nodes
- [[build_lab_replay_frames_for_project()]] - degree 22, connects to 9 communities
- [[get_latest_lab_replay_track_for_project()]] - degree 6, connects to 2 communities
- [[_solver_runtime_timeline_frames_for_run()]] - degree 6, connects to 2 communities
- [[_lab_timeline_frames_from_track()]] - degree 6, connects to 2 communities
- [[lab_replay_timeline_payload.py]] - degree 14, connects to 1 community