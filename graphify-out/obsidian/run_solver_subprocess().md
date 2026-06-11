---
source_file: "django_apps/asteroid_lab/services/solver_subprocess_runner.py"
type: "code"
community: "run_solver_subprocess()"
location: "L153"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/run_solver_subprocess
---

# run_solver_subprocess()

## Connections
- [[Invoke the CLI and copy the combined subprocess log into the final artifact.]] - `rationale_for` [EXTRACTED]
- [[Path]] - `calls` [EXTRACTED]
- [[SolverSubprocessError]] - `calls` [EXTRACTED]
- [[SolverSubprocessRequest_1]] - `references` [EXTRACTED]
- [[SolverSubprocessResult]] - `calls` [EXTRACTED]
- [[_run_subprocess_runtime_for_project()]] - `calls` [INFERRED]
- [[_write_inputs()]] - `calls` [EXTRACTED]
- [[build_solver_cli_args()]] - `calls` [EXTRACTED]
- [[resolve_subprocess_artifact_dir()]] - `calls` [EXTRACTED]
- [[run_subprocess_with_tee()]] - `calls` [INFERRED]
- [[solver_subprocess_runner.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/run_solver_subprocess