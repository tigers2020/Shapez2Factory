---
source_file: "django_apps/asteroid_lab/services/solver_runtime_entry.py"
type: "code"
community: "SolverRun"
location: "L171"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/SolverRun
---

# enqueue_solver_run_for_project()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[SolverEnqueueResult]] - `calls` [EXTRACTED]
- [[Spawn a detached CLI subprocess and return immediately (HTTP 202 path).]] - `rationale_for` [EXTRACTED]
- [[_build_subprocess_request()]] - `calls` [EXTRACTED]
- [[_latest_map_input()]] - `calls` [EXTRACTED]
- [[_run_solver_post_traced()]] - `calls` [INFERRED]
- [[create_running_solver_run()]] - `calls` [INFERRED]
- [[default_artifact_root()]] - `calls` [INFERRED]
- [[planned_artifact_dir()]] - `calls` [INFERRED]
- [[solver_runtime_entry.py]] - `contains` [EXTRACTED]
- [[spawn_solver_subprocess_detached()]] - `calls` [INFERRED]
- [[subprocess_sidecar_log_path()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/SolverRun