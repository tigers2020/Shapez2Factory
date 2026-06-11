---
source_file: "django_apps/asteroid_lab/services/subprocess_stream_tee.py"
type: "rationale"
community: "run_solver_subprocess()"
location: "L102"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/run_solver_subprocess
---

# Child process spawned without blocking the caller (log drain continues in daemon

## Connections
- [[DetachedSubprocessHandle]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/run_solver_subprocess