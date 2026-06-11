---
type: community
cohesion: 0.13
members: 23
---

# _run_artifact()

**Cohesion:** 0.13 - loosely connected
**Members:** 23 nodes

## Members
- [[CLI console observability formatter (BA-9, spec §11).  Emits one access-log-]] - rationale - src/shapez2_factory/adapters/asteroid_lab/cli_console.py
- [[Execute the pure stack and write a finalized artifact directory.]] - rationale - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[ExitCode]] - code - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[Fail-closed validation of a finalized artifact directory.]] - rationale - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[IntEnum]] - code
- [[Return whether BA-9 stderr one-liners should be emitted.      Default ON. Disa]] - rationale - src/shapez2_factory/adapters/asteroid_lab/cli_console.py
- [[Return whether optional per-layer CLI lines should be emitted.]] - rationale - src/shapez2_factory/adapters/asteroid_lab/cli_console.py
- [[Typed process exit codes for the ``asteroid_solve`` CLI.]] - rationale - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[Write a single BA-9 line to ``sys.stderr`` (no-op when logging disabled).]] - rationale - src/shapez2_factory/adapters/asteroid_lab/cli_console.py
- [[_json_bytes()]] - code - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[_read_copy_file()]] - code - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[_read_text_file()]] - code - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[_render_value()]] - code - src/shapez2_factory/adapters/asteroid_lab/cli_console.py
- [[_run_artifact()]] - code - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[``asteroid_solve`` CLI for pure-core artifact validation and solver runs.]] - rationale - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[asteroid_solve.py]] - code - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[build_parser()]] - code - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[cli_console.py]] - code - src/shapez2_factory/adapters/asteroid_lab/cli_console.py
- [[console_logging_enabled()]] - code - src/shapez2_factory/adapters/asteroid_lab/cli_console.py
- [[emit_cli_line()]] - code - src/shapez2_factory/adapters/asteroid_lab/cli_console.py
- [[main()]] - code - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[validate_artifact()]] - code - src/shapez2_factory/interfaces/cli/asteroid_solve.py
- [[verbose_logging_enabled()]] - code - src/shapez2_factory/adapters/asteroid_lab/cli_console.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/_run_artifact
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_Path]]
- 2 edges to [[_COMMUNITY_Exception]]
- 1 edge to [[_COMMUNITY_entry_result_to_json_dict()]]
- 1 edge to [[_COMMUNITY__run_solver_post_traced()]]
- 1 edge to [[_COMMUNITY_Enum]]
- 1 edge to [[_COMMUNITY_BaseCommand]]
- 1 edge to [[_COMMUNITY_AtomicArtifactWriter]]
- 1 edge to [[_COMMUNITY_write_replay_core_jsonl()]]

## Top bridge nodes
- [[_run_artifact()]] - degree 12, connects to 4 communities
- [[emit_cli_line()]] - degree 8, connects to 2 communities
- [[validate_artifact()]] - degree 5, connects to 2 communities
- [[build_parser()]] - degree 4, connects to 2 communities
- [[asteroid_solve.py]] - degree 10, connects to 1 community