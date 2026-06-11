---
source_file: "django_apps/asteroid_lab/replay/solver_runtime_assembler.py"
type: "code"
community: "build_solver_runtime_replay_frames()"
location: "L114"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/build_solver_runtime_replay_frames
---

# build_solver_runtime_replay_frames()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[IntegratedRimGreedyResult]] - `references` [EXTRACTED]
- [[JSON-serializable frames for ``SolverRun.config_jsonsolver_runtime_replay_frame]] - `rationale_for` [EXTRACTED]
- [[Layer04InnerFillResult]] - `references` [EXTRACTED]
- [[Layer04RimPlacementResult]] - `references` [EXTRACTED]
- [[Layer05RoutePlan]] - `references` [EXTRACTED]
- [[ReconstructionCompleteMap]] - `references` [EXTRACTED]
- [[RimBundleCandidateSet]] - `references` [EXTRACTED]
- [[_ensure_renderable_base_map_view()]] - `calls` [EXTRACTED]
- [[_finalize_specs()]] - `calls` [EXTRACTED]
- [[build_layer02_exterior_transport_frame()]] - `calls` [INFERRED]
- [[build_layer02_runtime_replay_frames()]] - `calls` [INFERRED]
- [[build_layer03_rim_greedy_runtime_segment_specs()]] - `calls` [INFERRED]
- [[build_layer03_runtime_segment_specs()]] - `calls` [INFERRED]
- [[build_layer04_inner_pattern_fill_frames()]] - `calls` [INFERRED]
- [[build_layer04_runtime_segment_specs()]] - `calls` [INFERRED]
- [[build_layer05_transport_frames()]] - `calls` [INFERRED]
- [[build_persistent_committed_equipment_overlay_wire()]] - `calls` [INFERRED]
- [[build_persistent_inner_fill_overlay_wire()]] - `calls` [INFERRED]
- [[build_solver_runtime_replay_frames_from_artifact_run()]] - `calls` [INFERRED]
- [[compose_runtime_overlay_wire()]] - `calls` [INFERRED]
- [[finalize_timeline_frame_to_json_dict()]] - `calls` [INFERRED]
- [[find_reconstruction_complete_source_frame()]] - `calls` [INFERRED]
- [[map_view_from_complete_map()]] - `calls` [INFERRED]
- [[persistent_connector_overlays_from_wire()]] - `calls` [INFERRED]
- [[replay_map_view_from_json_dict()]] - `calls` [INFERRED]
- [[solver_runtime_assembler.py]] - `contains` [EXTRACTED]
- [[structural_overlay_wire_from_source_frame()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/build_solver_runtime_replay_frames