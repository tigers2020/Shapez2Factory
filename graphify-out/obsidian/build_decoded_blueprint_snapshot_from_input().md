---
source_file: "django_apps/asteroid_lab/services/cell_snapshot_service.py"
type: "code"
community: "record_existing_layout_inspection_frames"
location: "L34"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/record_existing_layout_inspection_frames
---

# build_decoded_blueprint_snapshot_from_input()

## Connections
- [[DecodedBlueprintSnapshotDTO]] - `references` [EXTRACTED]
- [[Load ``AsteroidMapInput.decoded_json`` and build a pure snapshot DTO.]] - `rationale_for` [EXTRACTED]
- [[build_decoded_blueprint_snapshot()]] - `calls` [INFERRED]
- [[build_existing_layout_inspection_from_input()]] - `calls` [INFERRED]
- [[build_initial_replay_for_map_input()]] - `calls` [INFERRED]
- [[cell_snapshot_service.py]] - `contains` [EXTRACTED]
- [[record_existing_layout_inspection_frames()]] - `calls` [INFERRED]
- [[run_reconstruction_for_map_input()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/record_existing_layout_inspection_frames