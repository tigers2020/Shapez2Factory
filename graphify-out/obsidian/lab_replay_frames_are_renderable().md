---
source_file: "django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py"
type: "code"
community: "build_solver_runtime_replay_frames_from_"
location: "L50"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/build_solver_runtime_replay_frames_from_
---

# lab_replay_frames_are_renderable()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[True when frames carry a Lab ``map_view`` (not raw replay_core records).]] - `rationale_for` [EXTRACTED]
- [[_warm_lab_replay_cache_after_artifact_ingest()]] - `calls` [INFERRED]
- [[artifact_replay_viewer_compose.py]] - `contains` [EXTRACTED]
- [[asteroid_miner_layout_project_solver_run_lab_replay()]] - `calls` [INFERRED]
- [[compose_lab_replay_frames_from_artifact_run()]] - `calls` [EXTRACTED]
- [[lab_page_context()]] - `calls` [INFERRED]
- [[load_composed_frames_for_run_id()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/build_solver_runtime_replay_frames_from_