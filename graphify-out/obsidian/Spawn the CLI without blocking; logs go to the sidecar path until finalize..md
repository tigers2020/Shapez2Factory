---
source_file: "django_apps/asteroid_lab/services/solver_subprocess_runner.py"
type: "rationale"
community: "run_solver_subprocess()"
location: "L210"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/run_solver_subprocess
---

# Spawn the CLI without blocking; logs go to the sidecar path until finalize.

## Connections
- [[spawn_solver_subprocess_detached()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/run_solver_subprocess