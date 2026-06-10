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

# Plan: Document run_solver_reap cron interval in deploy docs

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Mid

## Problem

PR-CLI-7 lists reap cron as an expected concurrent caller alongside UI poll, but deploy docs and `scripts/render_start.sh` do not document the required schedule or interval.

## Scope

Document cron interval, command, and acceptance criteria in deploy/ops docs after infra wiring lands.

## Non-goals

- Changing reconcile semantics.
- Replacing UI polling documentation as primary path.

## Implementation Plan

1. After high-priority cron lands, add section to PR-CLI-7 plan or deploy README covering interval (1–5 min), command, and stale-RUNNING acceptance.
2. Note relationship to `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS`.
3. Link from `documents/ai/manuals/` if ops manual exists for Asteroid Lab deploy.

## Files / Areas Likely Affected

- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- `scripts/render_start.sh` (comment or README cross-link)
- TBD: deploy/ops doc path

## Validation Plan

- lint: N/A (docs)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Ops can follow doc to verify cron without reading source

## Acceptance Criteria

- [ ] Deploy/ops docs mention cron and interval.
- [ ] PR-CLI-7 expectation documented as met.

## Risks / Open Questions

- Staging vs production cron parity may need separate note.
