---
source_file: "django_apps/asteroid_lab/services/lab_replay_persisted_cache.py"
type: "code"
community: "lab_page_context()"
location: "L134"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/lab_page_context
---

# load_composed_frames_for_run_id()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[Load replay frames artifact-first, then dedicated DB cache, then legacy config.]] - `rationale_for` [EXTRACTED]
- [[_dict_or_none()]] - `calls` [EXTRACTED]
- [[_is_stale_thin_artifact_l3_cache()]] - `calls` [EXTRACTED]
- [[asteroid_miner_layout_project_solver_run_lab_replay()]] - `calls` [INFERRED]
- [[entry_result_to_json_dict()]] - `calls` [INFERRED]
- [[is_cache_summary_valid()]] - `calls` [EXTRACTED]
- [[lab_page_context()]] - `calls` [INFERRED]
- [[lab_replay_frames_are_renderable()]] - `calls` [INFERRED]
- [[lab_replay_persisted_cache.py]] - `contains` [EXTRACTED]
- [[replay_compose_cache_enabled()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/lab_page_context