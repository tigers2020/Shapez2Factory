---
source_file: "django_apps/asteroid_lab/services/lab_replay_lazy_handle.py"
type: "rationale"
community: "entry_result_to_json_dict()"
location: "L76"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/entry_result_to_json_dict
---

# Prefer the latest frame that still shows equipment; fall back to the last slot.

## Connections
- [[preview_frame_index_for_lab_replay()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/entry_result_to_json_dict