---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: M
pr: 7
related_docs:
  - documents/Algorithm/asteroid_lab_09_replay_debug.md
  - documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md
  - documents/Algorithm/solver_runtime/01_entry_point.md
---

# Phase M ? Persist / Replay / UI Payload

## Purpose

Reflect solver results to DB and UI. Lab replay and optimization replay are **not implicitly synchronized**.

> **PR7 = reuse forbidden:** [`asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md) persist/read/validation/HUD (12F?12L etc.) must **not be reimplemented**. Runtime Phase M events connect to existing writer/reader via **thin adapter** only ([`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) §6).

## Input

```text
ValidationResult
MaterializedLayoutCells
optimization run metrics
replay frames (accumulated)
```

## Output

```text
SolverRun.config_json (optimization_replay_frames, solver_summary, etc.)
UI: optimization replay track + layout preview
```

## Tasks

### Persist (reuse existing path)

```text
SolverRun.config_json          # existing Lab persist contract
optimization_replay_frames     # existing frame list validator?truncation policy reuse
solver_summary
materialized_layout preview
validation_result
```

Rule: Runtime orchestration calls **existing** attach/read API + records Runtime function subset of `OptimizationReplayEventType` (`django_apps/asteroid_lab/optimization/enums.py`).

### Replay event inventory

```text
optimization.input_loaded
capacity.plan_created
route_goal.generated
pattern.generated
candidate.generated
candidate.rejected
route_probe.succeeded
route_probe.failed
candidate_pool.completed
candidate_selection.completed
route.commit_attempted
route.committed
route.rolled_back
route.materialized
validation.completed
```

`OptimizationReplayEventType` enum ? algorithm input forbidden.

### UI

```text
Lab replay = map rendering authority
Optimization replay = metadata / overlay observation
No implicit sync
```

## Forbidden

- Using replay?NDJSON as solver/GA input
- Implicit Lab timeline ? optimization frame index sync ([`asteroid_lab_09`](../asteroid_lab_09_replay_debug.md) dual-track)

## Completion criteria

- [ ] After persist, `solver_run_id`?replay payload queryable
- [ ] Event sequence deterministic
- [ ] UI has optimization track attach (Lab reload not required)

## Prerequisite phase

```text
test_solver_button_pipeline_persists_result
test_solver_button_pipeline_emits_replay_events
test_solver_button_pipeline_validation_read_only
test_solver_button_pipeline_no_implicit_lab_optimization_sync
```

## Related code?documents

- [`django_apps/web/views/public_pages.py`](../../../django_apps/web/views/public_pages.py)
- [`asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md)
- [`asteroid_lab_13_replay_payload_scalability.md`](../asteroid_lab_13_replay_payload_scalability.md)

## Next Phase

None (pipeline end). Entry: [`01_entry_point.md`](01_entry_point.md).
