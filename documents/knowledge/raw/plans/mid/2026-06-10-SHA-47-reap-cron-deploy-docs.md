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

# Plan: Document run_solver_reap cron interval and PR-CLI-7 alignment

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Mid

## Problem

Deploy docs missing cron interval documentation. PR-CLI-7 lists reap cron as expected concurrent caller but infra does not implement it.

## Scope

Document cron interval, ops runbook, and link from PR-CLI-7 async solver plan.

## Non-goals

- Cron implementation (High plan).

## Implementation Plan

1. Update deploy/ops docs with cron schedule and troubleshooting for stale RUNNING rows.
2. Cross-link PR-CLI-7 plan acceptance criteria.
3. Note interaction with `ActiveRunExistsError` / one-active-run guard.

## Files / Areas Likely Affected

- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- Deploy docs (TBD path)

## Validation Plan

- manual verification: ops doc describes reap interval and verification steps

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- None.
