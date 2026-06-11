---
source_file: "django_apps/asteroid_lab/services/solver_subprocess_runner.py"
type: "code"
community: "run_solver_subprocess()"
location: "L67"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/run_solver_subprocess
---

# resolve_subprocess_artifact_dir()

## Connections
- [[Path]] - `calls` [EXTRACTED]
- [[SolverSubprocessError]] - `calls` [EXTRACTED]
- [[Validate ``run_key`` and ensure final artifact path stays under allowed root.]] - `rationale_for` [EXTRACTED]
- [[planned_artifact_dir()]] - `calls` [INFERRED]
- [[run_solver_subprocess()]] - `calls` [EXTRACTED]
- [[solver_subprocess_runner.py]] - `contains` [EXTRACTED]
- [[spawn_solver_subprocess_detached()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/run_solver_subprocess