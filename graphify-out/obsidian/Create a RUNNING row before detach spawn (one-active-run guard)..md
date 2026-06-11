---
source_file: "django_apps/asteroid_lab/services/solver_run_registry.py"
type: "rationale"
community: "SolverRun"
location: "L69"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/SolverRun
---

# Create a RUNNING row before detach spawn (one-active-run guard).

## Connections
- [[create_running_solver_run()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/SolverRun