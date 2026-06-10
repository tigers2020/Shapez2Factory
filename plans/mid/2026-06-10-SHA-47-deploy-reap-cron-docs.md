---
linear_issue: SHA-47
title: No scheduled run_solver_reap; orphaned RUNNING rows block async solver until manual poll
priority: Mid
labels:
  - bug
  - automation
  - infra
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: SHA-47 — Deploy docs and PR-CLI-7 reap cron documentation (Mid scope)

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Mid (from issue Priority Breakdown)

## Problem

PR-CLI-7 lists concurrent reconcile callers as "UI poll, refresh, reap cron, admin" but deploy docs do not document the required cron interval or wiring. Operators lack visibility into the reap schedule expectation.

## Scope

- Document cron interval and ops hook in deploy/PR-CLI-7 docs.
- Note PR-CLI-7 reap cron expectation in infra documentation.

## Non-goals

- Implementing the cron itself (see High plan `plans/high/2026-06-10-SHA-47-scheduled-run-solver-reap.md`).
- Health/monitoring for stale RUNNING rows (Low scope).

## Implementation Plan

1. Update `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md` with required `run_solver_reap` cron interval (1–5 min) and platform wiring notes.
2. Add deploy/ops section documenting how to verify cron is active and what happens when it is missing.
3. Cross-link from `AGENTS.md` or validation routine only if deploy docs are canonical entry — prefer focused deploy doc.
4. Include acceptance checklist: detached async run reconciled without browser poll.

## Files / Areas Likely Affected

- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- Deploy/ops doc path TBD (grep `render` / `run_solver_reap` in `documents/`)

## Validation Plan

- lint: N/A (docs)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Docs reviewer can follow steps to configure and verify cron

## Acceptance Criteria

- [ ] Matches the source issue spec Mid breakdown items.
- [ ] Stays within Mid priority scope (docs only).
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High plan landing cron wiring; docs should describe target state even if cron PR is separate.
