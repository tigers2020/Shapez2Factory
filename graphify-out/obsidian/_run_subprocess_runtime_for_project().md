---
source_file: "django_apps/asteroid_lab/services/solver_runtime_entry.py"
type: "code"
community: "entry_result_to_json_dict()"
location: "L75"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/entry_result_to_json_dict
---

# _run_subprocess_runtime_for_project()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[AsteroidMapInput]] - `references` [EXTRACTED]
- [[SolverRuntimeEntryResult]] - `calls` [EXTRACTED]
- [[SolverSubprocessError]] - `calls` [INFERRED]
- [[_build_subprocess_request()]] - `calls` [EXTRACTED]
- [[_empty_replay_track_metrics()]] - `calls` [EXTRACTED]
- [[default_artifact_root()]] - `calls` [INFERRED]
- [[ingest_artifact_for_project()]] - `calls` [INFERRED]
- [[run_solver_runtime_for_project()]] - `calls` [EXTRACTED]
- [[run_solver_subprocess()]] - `calls` [INFERRED]
- [[solver_runtime_entry.py]] - `contains` [EXTRACTED]
- [[validation_passed_from_solver_summary()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/entry_result_to_json_dict