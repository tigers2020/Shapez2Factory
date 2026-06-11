---
source_file: "django_apps/asteroid_lab/services/existing_layout_service.py"
type: "code"
community: "record_existing_layout_inspection_frames"
location: "L54"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/record_existing_layout_inspection_frames
---

# build_existing_layout_inspection_from_input()

## Connections
- [[ExistingLayoutInspectionDTO]] - `references` [EXTRACTED]
- [[Load ``AsteroidMapInput.decoded_json``, build A5 snapshot, inspect (does not mut]] - `rationale_for` [EXTRACTED]
- [[build_decoded_blueprint_snapshot_from_input()]] - `calls` [INFERRED]
- [[build_initial_replay_for_map_input()]] - `calls` [INFERRED]
- [[existing_layout_service.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/record_existing_layout_inspection_frames