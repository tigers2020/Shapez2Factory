---
type: community
cohesion: 0.11
members: 29
---

# run_solver_subprocess()

**Cohesion:** 0.11 - loosely connected
**Members:** 29 nodes

## Members
- [[Build the exact ``sys.executable -m ...`` invocation.]] - rationale - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[Child process spawned without blocking the caller (log drain continues in daemon]] - rationale - django_apps/asteroid_lab/services/subprocess_stream_tee.py
- [[Completed subprocess invocation plus resolved artifact paths.]] - rationale - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[Detached subprocess handle (caller must not wait on the child).]] - rationale - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[DetachedSubprocessHandle]] - code - django_apps/asteroid_lab/services/subprocess_stream_tee.py
- [[Django-side wrapper for invoking the Asteroid Lab pure CLI.]] - rationale - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[Input bundle needed to invoke the pure CLI solver.]] - rationale - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[Invoke the CLI and copy the combined subprocess log into the final artifact.]] - rationale - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[Raised when a subprocess run cannot be started safely or fails.]] - rationale - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[Result from a child process whose output was logged.]] - rationale - django_apps/asteroid_lab/services/subprocess_stream_tee.py
- [[Run a child process with ``shell=False`` and persist stdoutstderr.]] - rationale - django_apps/asteroid_lab/services/subprocess_stream_tee.py
- [[SolverSubprocessError]] - code - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[SolverSubprocessRequest_1]] - code - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[SolverSubprocessResult]] - code - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[SolverSubprocessSpawnResult]] - code - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[Spawn the CLI without blocking; logs go to the sidecar path until finalize.]] - rationale - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[Start child with shell=False; drain stdoutstderr to log_path without waiting.]] - rationale - django_apps/asteroid_lab/services/subprocess_stream_tee.py
- [[Subprocess execution with a durable combined stream log.]] - rationale - django_apps/asteroid_lab/services/subprocess_stream_tee.py
- [[SubprocessTeeResult]] - code - django_apps/asteroid_lab/services/subprocess_stream_tee.py
- [[Validate ``run_key`` and ensure final artifact path stays under allowed root.]] - rationale - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[_write_inputs()]] - code - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[build_solver_cli_args()]] - code - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[resolve_subprocess_artifact_dir()]] - code - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[run_solver_subprocess()]] - code - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[run_subprocess_with_tee()]] - code - django_apps/asteroid_lab/services/subprocess_stream_tee.py
- [[solver_subprocess_runner.py]] - code - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[spawn_solver_subprocess_detached()]] - code - django_apps/asteroid_lab/services/solver_subprocess_runner.py
- [[spawn_subprocess_with_log_tee()]] - code - django_apps/asteroid_lab/services/subprocess_stream_tee.py
- [[subprocess_stream_tee.py]] - code - django_apps/asteroid_lab/services/subprocess_stream_tee.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/run_solver_subprocess
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Path]]
- 3 edges to [[_COMMUNITY_SolverRun]]
- 2 edges to [[_COMMUNITY_entry_result_to_json_dict()]]
- 1 edge to [[_COMMUNITY_Exception]]

## Top bridge nodes
- [[run_solver_subprocess()]] - degree 11, connects to 2 communities
- [[spawn_solver_subprocess_detached()]] - degree 10, connects to 2 communities
- [[resolve_subprocess_artifact_dir()]] - degree 7, connects to 2 communities
- [[SolverSubprocessError]] - degree 6, connects to 2 communities
- [[solver_subprocess_runner.py]] - degree 11, connects to 1 community