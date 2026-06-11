---
type: community
cohesion: 0.12
members: 34
---

# build_solver_runtime_replay_frames()

**Cohesion:** 0.12 - loosely connected
**Members:** 34 nodes

## Members
- [[Central solver runtime replay frame assembler (L2→L3→L4 fill→L5; output-only).]] - rationale - django_apps/asteroid_lab/replay/solver_runtime_assembler.py
- [[Committed L4 interior occupancy carried on L5+ runtime frames.]] - rationale - django_apps/asteroid_lab/replay/layer04_inner_pattern_fill_segment.py
- [[Finalize solver-runtime replay frames (overlay wire + metrics; assembler-owned).]] - rationale - django_apps/asteroid_lab/replay/runtime_frame_finalize.py
- [[JSON-serializable frames for ``SolverRun.config_jsonsolver_runtime_replay_frame]] - rationale - django_apps/asteroid_lab/replay/solver_runtime_assembler.py
- [[Layer 04 inner pattern fill replay segment (canonical L4 slug).]] - rationale - django_apps/asteroid_lab/replay/layer04_inner_pattern_fill_segment.py
- [[Layer04InnerFillResult]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/run.py
- [[Non-connector overlay rows from reconstruction source only (not L2 display overl]] - rationale - django_apps/asteroid_lab/replay/runtime_frame_finalize.py
- [[ReplayMapView]] - code - django_apps/asteroid_lab/replay/timeline_serialization.py
- [[ReplaySegmentFrameSpec]] - code - django_apps/asteroid_lab/replay/solver_runtime_assembler.py
- [[Test helper timeline frames without wire overlay patch on map_view DTO.]] - rationale - django_apps/asteroid_lab/replay/runtime_frame_finalize.py
- [[True when the frame is not metadata-only (per replay timeline contract).]] - rationale - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[_ensure_renderable_base_map_view()]] - code - django_apps/asteroid_lab/replay/solver_runtime_assembler.py
- [[_extension_kind()]] - code - django_apps/asteroid_lab/replay/layer04_inner_pattern_fill_segment.py
- [[_finalize_specs()]] - code - django_apps/asteroid_lab/replay/solver_runtime_assembler.py
- [[_metrics_for_result()]] - code - django_apps/asteroid_lab/replay/layer04_inner_pattern_fill_segment.py
- [[_metrics_with_exterior_plan()]] - code - django_apps/asteroid_lab/replay/runtime_frame_finalize.py
- [[_miner_kind()]] - code - django_apps/asteroid_lab/replay/layer04_inner_pattern_fill_segment.py
- [[_overlay_cells_for_result()]] - code - django_apps/asteroid_lab/replay/layer04_inner_pattern_fill_segment.py
- [[_overlays_for_routeable_group()]] - code - django_apps/asteroid_lab/replay/layer04_inner_pattern_fill_segment.py
- [[_with_empty_reconstruction_base_ref()]] - code - django_apps/asteroid_lab/replay/solver_runtime_assembler.py
- [[build_layer04_inner_pattern_fill_frames()]] - code - django_apps/asteroid_lab/replay/layer04_inner_pattern_fill_segment.py
- [[build_persistent_inner_fill_overlay_wire()]] - code - django_apps/asteroid_lab/replay/layer04_inner_pattern_fill_segment.py
- [[build_solver_runtime_replay_frames()]] - code - django_apps/asteroid_lab/replay/solver_runtime_assembler.py
- [[compose_runtime_overlay_wire()]] - code - django_apps/asteroid_lab/replay/runtime_frame_finalize.py
- [[finalize_segment_spec_to_json_dict()]] - code - django_apps/asteroid_lab/replay/runtime_frame_finalize.py
- [[finalize_segment_spec_to_timeline_frame()]] - code - django_apps/asteroid_lab/replay/runtime_frame_finalize.py
- [[finalize_specs_to_timeline_frames()]] - code - django_apps/asteroid_lab/replay/runtime_frame_finalize.py
- [[finalize_timeline_frame_to_json_dict()]] - code - django_apps/asteroid_lab/replay/runtime_frame_finalize.py
- [[layer04_inner_pattern_fill_segment.py]] - code - django_apps/asteroid_lab/replay/layer04_inner_pattern_fill_segment.py
- [[replay_map_view_is_renderable()]] - code - django_apps/asteroid_lab/replay/timeline_dtos.py
- [[runtime_frame_finalize.py]] - code - django_apps/asteroid_lab/replay/runtime_frame_finalize.py
- [[solver_runtime_assembler.py]] - code - django_apps/asteroid_lab/replay/solver_runtime_assembler.py
- [[structural_overlay_wire_from_source_frame()]] - code - django_apps/asteroid_lab/replay/runtime_frame_finalize.py
- [[transient_overlay_cells_to_wire()]] - code - django_apps/asteroid_lab/replay/runtime_frame_finalize.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_solver_runtime_replay_frames
SORT file.name ASC
```

## Connections to other communities
- 8 edges to [[_COMMUNITY_timeline_serialization.py]]
- 8 edges to [[_COMMUNITY_ReplayEventType]]
- 7 edges to [[_COMMUNITY_ReplayOverlayCell]]
- 6 edges to [[_COMMUNITY_layer03_rim_greedy_segment.py]]
- 5 edges to [[_COMMUNITY_Any]]
- 5 edges to [[_COMMUNITY_build_layer02_timeline_frame_wire_dict()]]
- 4 edges to [[_COMMUNITY_route_layer04_sequential()]]
- 3 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 3 edges to [[_COMMUNITY_lab_timeline_adapter.py]]
- 3 edges to [[_COMMUNITY_build_layer03_runtime_segment_specs()]]
- 2 edges to [[_COMMUNITY_write_lab_solver_layer_stack_logs()]]
- 2 edges to [[_COMMUNITY_run_greedy_inner_fill()]]
- 2 edges to [[_COMMUNITY_wire_explicit_height_layer()]]
- 2 edges to [[_COMMUNITY_timeline_dtos.py]]
- 1 edge to [[_COMMUNITY_enrich_lab_timeline_frames_with_terrain_]]
- 1 edge to [[_COMMUNITY_build_solver_runtime_replay_frames_from_]]

## Top bridge nodes
- [[build_solver_runtime_replay_frames()]] - degree 28, connects to 11 communities
- [[ReplaySegmentFrameSpec]] - degree 15, connects to 4 communities
- [[ReplayMapView]] - degree 11, connects to 3 communities
- [[transient_overlay_cells_to_wire()]] - degree 6, connects to 3 communities
- [[Layer04InnerFillResult]] - degree 11, connects to 2 communities