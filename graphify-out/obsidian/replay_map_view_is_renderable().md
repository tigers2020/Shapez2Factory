---
source_file: "django_apps/asteroid_lab/replay/timeline_dtos.py"
type: "code"
community: "build_solver_runtime_replay_frames()"
location: "L99"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/build_solver_runtime_replay_frames
---

# replay_map_view_is_renderable()

## Connections
- [[ReplayMapView_1]] - `references` [EXTRACTED]
- [[True when the frame is not metadata-only (per replay timeline contract).]] - `rationale_for` [EXTRACTED]
- [[_build_map_view()]] - `calls` [INFERRED]
- [[_ensure_renderable_base_map_view()]] - `calls` [INFERRED]
- [[_with_empty_reconstruction_base_ref()]] - `calls` [INFERRED]
- [[finalize_segment_spec_to_timeline_frame()]] - `calls` [INFERRED]
- [[timeline_dtos.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/build_solver_runtime_replay_frames