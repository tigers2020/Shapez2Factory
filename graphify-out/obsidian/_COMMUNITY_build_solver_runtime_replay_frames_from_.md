---
type: community
cohesion: 0.14
members: 21
---

# build_solver_runtime_replay_frames_from_

**Cohesion:** 0.14 - loosely connected
**Members:** 21 nodes

## Members
- [[ArtifactManifestRecord]] - code - django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py
- [[Build renderable Lab frames from indexed artifact files; never algorithm input.]] - rationale - django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py
- [[Metrics wire serialization for exterior connector plans.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/wire.py
- [[Re-execute L2→L3→L4→L5 on artifact inputs and emit overlay-capable runtime repla]] - rationale - django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py
- [[True when frames carry a Lab ``map_view`` (not raw replay_core records).]] - rationale - django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py
- [[Viewer-only enrich artifact replay_core + complete_map into Lab timeline JSON (]] - rationale - django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py
- [[Viewer-only rebuild L2-L5 solver runtime replay frames from a CLI artifact (out]] - rationale - django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py
- [[_capacity_envelope()]] - code - django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py
- [[_load_complete_map()]] - code - django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py
- [[_load_genetic_sample_seeds()]] - code - django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py
- [[_load_solver_summary()]] - code - django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py
- [[_manifest_path()_1]] - code - django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py
- [[_timeline_frame_from_core_record()]] - code - django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py
- [[artifact_replay_viewer_compose.py]] - code - django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py
- [[artifact_runtime_replay_compose.py]] - code - django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py
- [[build_solver_runtime_replay_frames_from_artifact_run()]] - code - django_apps/asteroid_lab/services/artifact_runtime_replay_compose.py
- [[compose_lab_replay_frames_from_artifact_run()]] - code - django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py
- [[exterior_connector_plan_to_metrics_dict()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/wire.py
- [[lab_replay_frames_are_renderable()]] - code - django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py
- [[wire.py]] - code - django_apps/asteroid_lab/layers/layer_02_exterior_transport/wire.py
- [[wire.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/wire.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_solver_runtime_replay_frames_from_
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Any]]
- 6 edges to [[_COMMUNITY_Path]]
- 5 edges to [[_COMMUNITY_lab_page_context()]]
- 4 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 4 edges to [[_COMMUNITY_ingest_artifact_for_project()]]
- 3 edges to [[_COMMUNITY_timeline_serialization.py]]
- 2 edges to [[_COMMUNITY_ExteriorConnectionPlan]]
- 2 edges to [[_COMMUNITY_build_layer02_timeline_frame_wire_dict()]]
- 2 edges to [[_COMMUNITY_read_verified_artifact_manifest()]]
- 2 edges to [[_COMMUNITY_SolverRun]]
- 1 edge to [[_COMMUNITY_GameDataRulesPort]]
- 1 edge to [[_COMMUNITY_build_solver_runtime_replay_frames()]]
- 1 edge to [[_COMMUNITY_complete_map_serializer.py]]
- 1 edge to [[_COMMUNITY_build_lab_replay_frames_for_project()]]
- 1 edge to [[_COMMUNITY_run_layers_02_to_06()]]
- 1 edge to [[_COMMUNITY_run_greedy_inner_fill()]]
- 1 edge to [[_COMMUNITY_route_layer04_sequential()]]
- 1 edge to [[_COMMUNITY_try_load_default_space_transport_catalog]]

## Top bridge nodes
- [[build_solver_runtime_replay_frames_from_artifact_run()]] - degree 20, connects to 12 communities
- [[compose_lab_replay_frames_from_artifact_run()]] - degree 15, connects to 8 communities
- [[_timeline_frame_from_core_record()]] - degree 6, connects to 4 communities
- [[lab_replay_frames_are_renderable()]] - degree 8, connects to 3 communities
- [[_load_complete_map()]] - degree 6, connects to 3 communities