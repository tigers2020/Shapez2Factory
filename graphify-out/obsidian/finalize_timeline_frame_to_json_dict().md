---
source_file: "django_apps/asteroid_lab/replay/runtime_frame_finalize.py"
type: "code"
community: "build_solver_runtime_replay_frames()"
location: "L120"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/build_solver_runtime_replay_frames
---

# finalize_timeline_frame_to_json_dict()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[ReplayTimelineFrame]] - `references` [EXTRACTED]
- [[_metrics_with_exterior_plan()]] - `calls` [EXTRACTED]
- [[build_solver_runtime_replay_frames()]] - `calls` [INFERRED]
- [[finalize_segment_spec_to_json_dict()]] - `calls` [EXTRACTED]
- [[replay_timeline_frame_to_json_dict()]] - `calls` [INFERRED]
- [[runtime_frame_finalize.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/build_solver_runtime_replay_frames