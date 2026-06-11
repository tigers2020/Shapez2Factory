---
source_file: "django_apps/web/services/replay_frame_cell_lookup.py"
type: "rationale"
community: "replay_frame_cell_lookup.py"
location: "L154"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/replay_frame_cell_lookuppy
---

# Paint order: full_map + diff; else overlay; else bbox-empty synthetic cell.

## Connections
- [[lookup_cell_in_serialized_frame()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/replay_frame_cell_lookuppy