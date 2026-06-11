---
source_file: "django_apps/asteroid_lab/services/subprocess_stream_tee.py"
type: "rationale"
community: "run_solver_subprocess()"
location: "L34"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/run_solver_subprocess
---

# Run a child process with ``shell=False`` and persist stdout/stderr.

## Connections
- [[run_subprocess_with_tee()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/run_solver_subprocess