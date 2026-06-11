---
linear_issue: SHA-36
title: CLI RunStackUseCase omits layer_01_reconstruction from layer_summaries and replay_core
priority: Low
labels:
  - bug
  - solver
  - reviewing
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: reconstruction_capacity authority alignment (SHA-36 Low)

## Source Issue

- Linear: SHA-36
- Status at planning time: Todo
- Priority: Low

## Problem

Even after CLI L1 layer summaries are wired (Mid plan), `reconstruction_capacity.by_resource.authority` may still drift between `game_data_snapshot` and `MiningExtractionRule` sources. Lab UI partially compensates via heuristics on `reconstruction_capacity`, but artifact truth for authority provenance remains inconsistent.

## Scope

- Audit and align `reconstruction_capacity.by_resource.authority` values between CLI and Django L1 paths.
- Document canonical authority source in observability metrics or artifact schema.

## Non-goals

- CLI L1 layer_summaries / replay_core wiring (Mid plan).
- Changing Django stack_runner L1 behavior beyond authority field alignment.
- L6 validation stub (SHA-15).

## Implementation Plan

1. Compare L1 capacity envelope construction in `src/shapez2_factory/application/asteroid_lab/run_stack.py` vs `django_apps/asteroid_lab/layers/stack_runner.py`.
2. Trace `reconstruction_capacity` fields through `post_summary_metrics.py` and any game_data snapshot loaders.
3. Define single authority enum/source for `by_resource.authority` and apply in both CLI and Django metric builders.
4. Add regression test asserting authority field matches expected catalog source for a fixture run.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py`
- `django_apps/asteroid_lab/layers/stack_runner.py`
- TBD — game_data snapshot / mining rule modules if authority is sourced there

## Validation Plan

- lint: `ruff check` on touched files
- typecheck: spot-check if authority types change
- tests: targeted pytest on L1 metrics authority field
- build: N/A
- manual verification: CLI and Django runs on same fixture show identical `reconstruction_capacity.by_resource.authority`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan landing for L1 summary presence; authority fix may be easier once L1 metrics are emitted.
- May overlap SHA-28 game_data provenance wiring — coordinate to avoid duplicate authority sources.
