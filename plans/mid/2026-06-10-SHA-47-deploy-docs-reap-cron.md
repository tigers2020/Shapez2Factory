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

# Plan: Document run_solver_reap cron in deploy and PR-CLI-7 docs

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Mid

## Problem

Deploy docs and PR-CLI-7 checklist do not document that `run_solver_reap` must run on a schedule in production. Operators have no canonical interval, command, or acceptance procedure. PR-CLI-7 lists reap cron as a concurrent reconcile caller but infra expectation is unmet in documentation.

## Scope

Document the reap cron interval, command, hosting mechanism, and staging acceptance steps. Cross-link from PR-CLI-7 plan/checklist and deployment manuals.

## Non-goals

- Changing reconcile semantics
- Replacing UI status polling
- Implementing monitoring (see Low plan)

## Implementation Plan

1. Update `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`:
   - Add **Operations** subsection under P0: cron schedule, `manage.py run_solver_reap`, concurrent callers table already mentions reap cron — add explicit "required in production" note and link to deploy doc.
2. Update `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/checklist.md`:
   - Add unchecked item: production/staging cron for `run_solver_reap` (depends on High plan landing).
3. Add deploy section to `documents/ai/manuals/environment.md` or new `documents/ai/manuals/deployment.md` (if deployment.md exists, extend; else add subsection to environment.md):
   - Cron command: `bash scripts/render_reap_cron.sh` or `python manage.py run_solver_reap`
   - Recommended interval: 2 minutes (within 1–5 min issue spec)
   - Setting: `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` — explain relationship to max stale RUNNING duration
   - Acceptance: detached async run reconciled without browser poll
4. Update `structure.md` if it lists management commands — note scheduled reap as ops requirement.
5. After High plan merges, verify doc paths match actual `render.yaml` / Render dashboard config.

## Files / Areas Likely Affected

- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/checklist.md`
- `documents/ai/manuals/environment.md` or `documents/ai/manuals/deployment.md`
- `structure.md`
- `scripts/render_reap_cron.sh` (link target from High plan)

## Validation Plan

- lint: N/A (docs only)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Doc review — interval, command, and acceptance steps match High plan infra

## Acceptance Criteria

- [ ] Deploy/ops docs mention the cron and interval.
- [ ] PR-CLI-7 reap cron expectation documented as production requirement.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope (documentation only).
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Docs must not claim cron exists until High plan infra is merged — use conditional wording or land docs in same PR as cron wiring.
- `deployment.md` may not exist; prefer smallest doc touch that satisfies acceptance.
