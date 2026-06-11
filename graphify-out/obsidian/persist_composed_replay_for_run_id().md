---
source_file: "django_apps/asteroid_lab/services/lab_replay_persisted_cache.py"
type: "code"
community: "lab_page_context()"
location: "L183"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/lab_page_context
---

# persist_composed_replay_for_run_id()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[Fresh read-merge-write; preserve unrelated ``config_json`` keys (§4.8).]] - `rationale_for` [EXTRACTED]
- [[_artifact_replay_source_snapshot()]] - `calls` [EXTRACTED]
- [[_dict_or_none()]] - `calls` [EXTRACTED]
- [[_warm_lab_replay_cache_after_artifact_ingest()]] - `calls` [INFERRED]
- [[asteroid_miner_layout_project_solver_run_lab_replay()]] - `calls` [INFERRED]
- [[build_manifest_summary_from_compose()]] - `calls` [EXTRACTED]
- [[lab_page_context()]] - `calls` [INFERRED]
- [[lab_replay_persisted_cache.py]] - `contains` [EXTRACTED]
- [[replay_compose_cache_enabled()]] - `calls` [EXTRACTED]
- [[sync_solver_run_fast_cache_from_config_json()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/lab_page_context