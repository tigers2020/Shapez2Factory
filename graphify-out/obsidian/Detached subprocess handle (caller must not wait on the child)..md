---
source_file: "django_apps/asteroid_lab/services/solver_subprocess_runner.py"
type: "rationale"
community: "run_solver_subprocess()"
location: "L59"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/run_solver_subprocess
---

# Detached subprocess handle (caller must not wait on the child).

## Connections
- [[SolverSubprocessSpawnResult]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/run_solver_subprocess