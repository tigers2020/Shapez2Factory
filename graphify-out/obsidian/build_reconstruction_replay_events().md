---
source_file: "django_apps/asteroid_lab/replay/reconstruction_frames.py"
type: "code"
community: "record_existing_layout_inspection_frames"
location: "L89"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/record_existing_layout_inspection_frames
---

# build_reconstruction_replay_events()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[CleanupResult]] - `references` [EXTRACTED]
- [[Convert trace events into persisted replay frames (full_map + diff per step).]] - `rationale_for` [EXTRACTED]
- [[ReconstructionResult]] - `references` [EXTRACTED]
- [[ReconstructionTraceEvent]] - `references` [EXTRACTED]
- [[SnapshotEventDTO]] - `calls` [EXTRACTED]
- [[_snapshot_event_type_for_trace()]] - `calls` [EXTRACTED]
- [[_sort_rows()]] - `calls` [EXTRACTED]
- [[_title_for_trace()]] - `calls` [EXTRACTED]
- [[_trace_marker_row()]] - `calls` [EXTRACTED]
- [[cell_key_xy_layer()]] - `calls` [INFERRED]
- [[decoded_cell_to_full_map_row()]] - `calls` [INFERRED]
- [[diff_maps()]] - `calls` [INFERRED]
- [[merge_reconstruction_display_rows()]] - `calls` [INFERRED]
- [[reconstruction_frames.py]] - `contains` [EXTRACTED]
- [[record_existing_layout_inspection_frames()]] - `calls` [INFERRED]
- [[snapshot_summary_from_rows()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/record_existing_layout_inspection_frames