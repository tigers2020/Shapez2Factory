---
source_file: "django_apps/asteroid_lab/services/solver_subprocess_runner.py"
type: "code"
community: "SolverRun"
location: "L88"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/SolverRun
---

# default_artifact_root()

## Connections
- [[Path]] - `calls` [EXTRACTED]
- [[Return the configured Django artifact root for CLI subprocess runs.]] - `rationale_for` [EXTRACTED]
- [[_artifact_dir_for_run()]] - `calls` [INFERRED]
- [[_run_subprocess_runtime_for_project()]] - `calls` [INFERRED]
- [[_sidecar_path_for_run()]] - `calls` [INFERRED]
- [[create_running_solver_run()]] - `calls` [INFERRED]
- [[enqueue_solver_run_for_project()]] - `calls` [INFERRED]
- [[solver_subprocess_runner.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/SolverRun