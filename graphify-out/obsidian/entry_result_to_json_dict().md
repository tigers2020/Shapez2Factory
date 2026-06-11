---
source_file: "django_apps/asteroid_lab/services/solver_runtime_entry.py"
type: "code"
community: "entry_result_to_json_dict()"
location: "L349"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/entry_result_to_json_dict
---

# entry_result_to_json_dict()

## Connections
- [[._handle_logged()]] - `calls` [INFERRED]
- [[Any]] - `references` [EXTRACTED]
- [[SolverRuntimeEntryResult]] - `references` [EXTRACTED]
- [[_normalize_milestone_track_metrics()]] - `calls` [EXTRACTED]
- [[_run_solver_post_traced()]] - `calls` [INFERRED]
- [[build_lab_replay_lazy_handle()]] - `calls` [INFERRED]
- [[build_lab_replay_lazy_handle_from_summary()]] - `calls` [INFERRED]
- [[is_cache_summary_valid()]] - `calls` [INFERRED]
- [[lab_replay_payload_mode()]] - `calls` [INFERRED]
- [[lab_run_summary_from_orm()]] - `calls` [INFERRED]
- [[load_composed_frames_for_run_id()]] - `calls` [INFERRED]
- [[load_manifest_summary_for_run_id()]] - `calls` [INFERRED]
- [[solver_runtime_entry.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/entry_result_to_json_dict