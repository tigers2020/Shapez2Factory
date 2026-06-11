---
source_file: "django_apps/asteroid_lab/services/lab_replay_persisted_cache.py"
type: "rationale"
community: "lab_page_context()"
location: "L189"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/lab_page_context
---

# Fresh read-merge-write; preserve unrelated ``config_json`` keys (§4.8).

## Connections
- [[persist_composed_replay_for_run_id()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/lab_page_context