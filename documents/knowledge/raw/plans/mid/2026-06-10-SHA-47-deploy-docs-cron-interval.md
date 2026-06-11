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

# Plan: Document run_solver_reap cron interval in deploy and PR-CLI-7 docs

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Mid

## Problem

Deploy docs do not mention the required `run_solver_reap` cron or its interval. PR-CLI-7 lists reap cron as a concurrent reconcile caller, but infra expectation is unmet and undocumented for operators.

## Scope

Document the cron schedule, command, interval rationale, and staging acceptance steps. Cross-link from PR-CLI-7 plan and any Render/deploy README.

## Non-goals

- Do not change reconcile semantics.
- Do not add monitoring dashboards (see Low plan).

## Implementation Plan

1. Identify canonical deploy doc (e.g. `scripts/render_build.sh` header comments, `structure.md`, or new `docs/deploy/render.md` if none exists).
2. Add section **Solver reap cron** covering:
   - Command: `python manage.py run_solver_reap`
   - Recommended interval: every 5 minutes (`*/5 * * * *`)
   - Dependency: same DB/env as web app
   - Setting: `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` controls timeout inside reconcile
   - Acceptance: orphaned RUNNING run reaped without browser poll
3. Update `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md` — in **Docs (on implement)** or reap section, link to deploy doc and note cron is required for P0 production.
4. Update `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/checklist.md` PR-CLI-7 item if reap cron checkbox is missing.
5. Add deploy-doc acceptance checklist item mirroring issue acceptance criteria.

## Files / Areas Likely Affected

- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/checklist.md`
- `scripts/render_start.sh` (comment cross-link only, optional)
- `structure.md` (ops index line for `run_solver_reap`)
- TBD: dedicated deploy doc path if created

## Validation Plan

- lint: N/A (docs-only)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Reader can configure Render cron from doc alone; links resolve in repo

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Deploy/ops docs mention the cron and interval.
- [ ] PR-CLI-7 references deploy cron documentation.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- If High plan chooses non-Render cron, docs must match actual host commands.
- Keep docs-only; do not claim cron is live until High plan is deployed.
