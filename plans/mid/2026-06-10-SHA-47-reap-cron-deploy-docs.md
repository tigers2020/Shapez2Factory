---
linear_issue: SHA-47
title: No scheduled run_solver_reap; orphaned RUNNING rows block async solver until manual poll
priority: Mid
labels:
  - automation
  - infra
  - priority:high
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: run_solver_reap deploy documentation

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Mid

## Problem

Deploy docs do not document the required `run_solver_reap` cron interval. PR-CLI-7 lists reap cron as an expected concurrent caller but infra wiring is missing from operator docs.

## Scope

Document cron interval, invocation command, and acceptance scenario in deploy/ops docs after High-priority cron wiring lands.

## Non-goals

- Changing reconcile semantics
- Implementing monitoring dashboards

## Implementation Plan

1. Add deploy section describing `run_solver_reap` schedule, interval, and environment parity with web app.
2. Cross-link PR-CLI-7 plan and SHA-47 High plan.
3. Document manual fallback: `python manage.py run_solver_reap` for ops.

## Files / Areas Likely Affected

- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- Deploy/ops docs (TBD — `structure.md` or host-specific README)
- `scripts/render_start.sh` comments

## Validation Plan

- lint: N/A (docs)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: operator can find cron docs and interval without reading source

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High plan cron wiring completing first.
