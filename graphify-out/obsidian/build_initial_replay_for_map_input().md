---
source_file: "django_apps/asteroid_lab/services/replay_pipeline_service.py"
type: "code"
community: "build_initial_replay_for_map_input()"
location: "L90"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/build_initial_replay_for_map_input
---

# build_initial_replay_for_map_input()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[Decode copy text, persist JSON, scaffold SolverRunReplayTrack, record inspectio]] - `rationale_for` [EXTRACTED]
- [[InitialReplayPipelineResultDTO]] - `calls` [EXTRACTED]
- [[_default_run_key()]] - `calls` [EXTRACTED]
- [[_latest_cell_snapshot_pk()]] - `calls` [EXTRACTED]
- [[_latest_reconstructed_map_pk()]] - `calls` [EXTRACTED]
- [[_result_from_completed_track()]] - `calls` [EXTRACTED]
- [[asteroid_miner_layout_create_project()]] - `calls` [INFERRED]
- [[build_decoded_blueprint_snapshot_from_input()]] - `calls` [INFERRED]
- [[build_existing_layout_inspection_from_input()]] - `calls` [INFERRED]
- [[content_sha256_for_copy_code()]] - `calls` [INFERRED]
- [[decode_copy_string()]] - `calls` [INFERRED]
- [[normalize_decoded_blueprint()]] - `calls` [INFERRED]
- [[persist_decoded_cell_snapshot()]] - `calls` [INFERRED]
- [[persist_decoded_snapshot_for_map_input()]] - `calls` [INFERRED]
- [[persist_existing_layout_inspection_snapshot()]] - `calls` [INFERRED]
- [[persist_reconstructed_asteroid_map()]] - `calls` [INFERRED]
- [[record_decoded_snapshot_frames()]] - `calls` [INFERRED]
- [[record_existing_layout_inspection_frames()]] - `calls` [INFERRED]
- [[replay_pipeline_service.py]] - `contains` [EXTRACTED]
- [[reset_project_map_to_inspection_clean()]] - `calls` [INFERRED]
- [[resolve_inspection_solver_run()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/build_initial_replay_for_map_input