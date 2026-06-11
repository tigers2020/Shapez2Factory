---
source_file: "django_apps/web/views/public_pages.py"
type: "code"
community: "_run_solver_post_traced()"
location: "L726"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/_run_solver_post_traced
---

# asteroid_miner_layout_replay_frame_cell()

## Connections
- [[HttpRequest]] - `references` [EXTRACTED]
- [[JsonResponse]] - `calls` [EXTRACTED]
- [[POST JSON resolve one cell at world (x, y) for a persisted class`ReplayFrame`]] - `rationale_for` [EXTRACTED]
- [[lookup_cell_in_serialized_frame()]] - `calls` [INFERRED]
- [[public_pages.py]] - `contains` [EXTRACTED]
- [[serialize_replay_frame()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/_run_solver_post_traced