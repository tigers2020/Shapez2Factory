---
source_file: "django_apps/asteroid_lab/services/subprocess_stream_tee.py"
type: "code"
community: "run_solver_subprocess()"
location: "L108"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/run_solver_subprocess
---

# spawn_subprocess_with_log_tee()

## Connections
- [[DetachedSubprocessHandle]] - `calls` [EXTRACTED]
- [[Path]] - `references` [EXTRACTED]
- [[Start child with shell=False; drain stdoutstderr to log_path without waiting.]] - `rationale_for` [EXTRACTED]
- [[spawn_solver_subprocess_detached()]] - `calls` [INFERRED]
- [[subprocess_stream_tee.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/run_solver_subprocess