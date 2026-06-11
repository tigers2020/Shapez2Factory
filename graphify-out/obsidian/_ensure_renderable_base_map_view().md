---
source_file: "django_apps/asteroid_lab/replay/solver_runtime_assembler.py"
type: "code"
community: "build_solver_runtime_replay_frames()"
location: "L81"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/build_solver_runtime_replay_frames
---

# _ensure_renderable_base_map_view()

## Connections
- [[ReconstructionCompleteMap]] - `references` [EXTRACTED]
- [[ReplayMapView]] - `references` [EXTRACTED]
- [[_with_empty_reconstruction_base_ref()]] - `calls` [EXTRACTED]
- [[build_solver_runtime_replay_frames()]] - `calls` [EXTRACTED]
- [[map_view_from_complete_map()]] - `calls` [INFERRED]
- [[replay_map_view_is_renderable()]] - `calls` [INFERRED]
- [[solver_runtime_assembler.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/build_solver_runtime_replay_frames