---
source_file: "django_apps/asteroid_lab/services/solver_subprocess_runner.py"
type: "code"
community: "run_solver_subprocess()"
location: "L204"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/run_solver_subprocess
---

# spawn_solver_subprocess_detached()

## Connections
- [[Path]] - `calls` [EXTRACTED]
- [[SolverSubprocessRequest_1]] - `references` [EXTRACTED]
- [[SolverSubprocessSpawnResult]] - `calls` [EXTRACTED]
- [[Spawn the CLI without blocking; logs go to the sidecar path until finalize.]] - `rationale_for` [EXTRACTED]
- [[_write_inputs()]] - `calls` [EXTRACTED]
- [[build_solver_cli_args()]] - `calls` [EXTRACTED]
- [[enqueue_solver_run_for_project()]] - `calls` [INFERRED]
- [[resolve_subprocess_artifact_dir()]] - `calls` [EXTRACTED]
- [[solver_subprocess_runner.py]] - `contains` [EXTRACTED]
- [[spawn_subprocess_with_log_tee()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/run_solver_subprocess