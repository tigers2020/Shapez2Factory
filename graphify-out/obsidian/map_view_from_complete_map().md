---
source_file: "django_apps/asteroid_lab/replay/layer02_segment.py"
type: "code"
community: "build_layer02_timeline_frame_wire_dict()"
location: "L28"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/build_layer02_timeline_frame_wire_dict
---

# map_view_from_complete_map()

## Connections
- [[ReconstructionCompleteMap]] - `references` [EXTRACTED]
- [[ReplayMapView]] - `references` [EXTRACTED]
- [[_bbox_from_rows()]] - `calls` [EXTRACTED]
- [[_display_rows_from_complete_map()]] - `calls` [EXTRACTED]
- [[_ensure_renderable_base_map_view()]] - `calls` [INFERRED]
- [[_timeline_frame_from_core_record()]] - `calls` [INFERRED]
- [[build_solver_runtime_replay_frames()]] - `calls` [INFERRED]
- [[build_solver_runtime_replay_frames_from_artifact_run()]] - `calls` [INFERRED]
- [[layer02_segment.py]] - `contains` [EXTRACTED]
- [[replay_map_view_from_json_dict()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/build_layer02_timeline_frame_wire_dict