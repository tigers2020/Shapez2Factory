---
source_file: "django_apps/asteroid_lab/replay/runtime_frame_finalize.py"
type: "code"
community: "build_solver_runtime_replay_frames()"
location: "L84"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/build_solver_runtime_replay_frames
---

# finalize_segment_spec_to_timeline_frame()

## Connections
- [[ReplayMapView]] - `calls` [EXTRACTED]
- [[ReplaySegmentFrameSpec]] - `references` [EXTRACTED]
- [[ReplayTimelineFrame]] - `calls` [EXTRACTED]
- [[_metrics_with_exterior_plan()]] - `calls` [EXTRACTED]
- [[finalize_segment_spec_to_json_dict()]] - `calls` [EXTRACTED]
- [[finalize_specs_to_timeline_frames()]] - `calls` [EXTRACTED]
- [[replay_map_view_is_renderable()]] - `calls` [INFERRED]
- [[runtime_frame_finalize.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/build_solver_runtime_replay_frames