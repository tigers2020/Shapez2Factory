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

# Plan: Document reap cron interval and PR-CLI-7 alignment

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Mid

## Problem

Deploy docs and PR-CLI-7 list reap cron as expected production caller but infra wiring and interval are undocumented.

## Scope

Document cron interval, environment requirements, and link from PR-CLI-7 / deploy docs after high-priority schedule lands.

## Non-goals

- Changing reconcile semantics
- Replacing UI polling

## Implementation Plan

1. Add ops section to `pr-cli-7-async-solver-job.md` or `documents/ai/manuals/` deploy notes.
2. State cron interval, command, and expected max stale RUNNING duration.
3. Cross-link from `scripts/render_start.sh` comment if applicable.

## Files / Areas Likely Affected

- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- deploy/ops documentation
- `scripts/render_start.sh` (comment only)

## Validation Plan

- manual verification: docs match actual cron config

## Acceptance Criteria

- [ ] Deploy/ops docs mention cron and interval.
- [ ] PR-CLI-7 expectation met in documentation.

## Risks / Open Questions

- Docs drift if cron moved to external infra — keep single source of truth.
