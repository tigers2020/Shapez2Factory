---
source_file: "django_apps/asteroid_lab/services/cell_snapshot_service.py"
type: "code"
community: "record_existing_layout_inspection_frames"
location: "L70"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/record_existing_layout_inspection_frames
---

# record_decoded_snapshot_frames()

## Connections
- [[Append decode replay frames raw full map, then transport-stripped map + removal]] - `rationale_for` [EXTRACTED]
- [[DecodedBlueprintSnapshotDTO]] - `references` [EXTRACTED]
- [[ReplayRecorder]] - `calls` [INFERRED]
- [[SnapshotFrameDTO]] - `references` [EXTRACTED]
- [[build_cleanup_and_reconstruction_rows()]] - `calls` [INFERRED]
- [[build_initial_replay_for_map_input()]] - `calls` [INFERRED]
- [[cell_snapshot_service.py]] - `contains` [EXTRACTED]
- [[decode_snapshot_summary()]] - `calls` [INFERRED]
- [[diff_maps()]] - `calls` [INFERRED]
- [[snapshot_summary_from_rows()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/record_existing_layout_inspection_frames