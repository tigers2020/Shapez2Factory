---
source_file: "django_apps/asteroid_lab/services/lab_replay_persisted_cache.py"
type: "rationale"
community: "lab_page_context()"
location: "L135"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/lab_page_context
---

# Load replay frames artifact-first, then dedicated DB cache, then legacy config.

## Connections
- [[load_composed_frames_for_run_id()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/lab_page_context