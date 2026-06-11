---
source_file: "django_apps/asteroid_lab/replay/runtime_frame_finalize.py"
type: "code"
community: "build_solver_runtime_replay_frames()"
location: "L137"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/build_solver_runtime_replay_frames
---

# finalize_segment_spec_to_json_dict()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[ReplayMapView]] - `references` [EXTRACTED]
- [[ReplaySegmentFrameSpec]] - `references` [EXTRACTED]
- [[_finalize_specs()]] - `calls` [INFERRED]
- [[compose_runtime_overlay_wire()]] - `calls` [EXTRACTED]
- [[finalize_segment_spec_to_timeline_frame()]] - `calls` [EXTRACTED]
- [[finalize_timeline_frame_to_json_dict()]] - `calls` [EXTRACTED]
- [[runtime_frame_finalize.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/build_solver_runtime_replay_frames