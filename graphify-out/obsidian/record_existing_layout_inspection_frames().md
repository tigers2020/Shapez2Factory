---
source_file: "django_apps/asteroid_lab/services/existing_layout_service.py"
type: "code"
community: "record_existing_layout_inspection_frames"
location: "L61"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/record_existing_layout_inspection_frames
---

# record_existing_layout_inspection_frames()

## Connections
- [[Append cleanup frames plus stepwise reconstruction replay (UI-only; never solver]] - `rationale_for` [EXTRACTED]
- [[CleanupResult]] - `references` [EXTRACTED]
- [[ExistingLayoutInspectionDTO]] - `references` [EXTRACTED]
- [[ReconstructionResult]] - `references` [EXTRACTED]
- [[ReplayRecorder]] - `calls` [INFERRED]
- [[SnapshotFrameDTO]] - `references` [EXTRACTED]
- [[_cell_overlay_with_equipment_bundles()]] - `calls` [EXTRACTED]
- [[build_cleanup_and_reconstruction_rows()]] - `calls` [INFERRED]
- [[build_decoded_blueprint_snapshot_from_input()]] - `calls` [INFERRED]
- [[build_initial_replay_for_map_input()]] - `calls` [INFERRED]
- [[build_reconstruction_replay_events()]] - `calls` [INFERRED]
- [[diff_maps()]] - `calls` [INFERRED]
- [[existing_layout_service.py]] - `contains` [EXTRACTED]
- [[reconstruction_acceptance_ok()]] - `calls` [INFERRED]
- [[rows_from_cells()]] - `calls` [INFERRED]
- [[run_reconstruction_for_map_input()]] - `calls` [INFERRED]
- [[snapshot_summary_from_rows()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/record_existing_layout_inspection_frames