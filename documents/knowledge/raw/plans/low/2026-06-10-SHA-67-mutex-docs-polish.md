---
linear_issue: SHA-67
title: "[automation] Project review run mutex via dedicated Linear holder card"
priority: Low
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Polish project-review run report and cross-link mutex docs

## Source Issue

- Linear: SHA-67
- Status at planning time: Todo
- Priority: Low

## Problem

Project-review automation run reports lack a consistent final summary format. Mutex documentation is not cross-linked from `daily-project-inspection-log.md`, making operator discovery harder.

## Scope

Standardize the automation final run report template and add cross-links between inspection log and mutex/holder-card documentation.

## Non-goals

- Do not change mutex behavior or stale-lock window.
- Do not refactor unrelated agent-workflow docs.

## Implementation Plan

1. Define a final run report block for project-review automation:

   ```text
   Status: complete | partial | blocked
   Trigger: project-review cron | manual
   Mutex holder: SHA-67
   Lock label: auto:project-review-running (added/removed)
   Reviewed area: <path/module>
   Findings filed: SHA-NN, ...
   Memory updated: yes | no
   Blocked/skipped: <reason>
   ```

2. Add the report template to the project-review automation prompt and to `docs/agent-workflows/daily-project-inspection-log.md` (or `project-review-mutex.md` if created in Mid plan).
3. Cross-link from `daily-project-inspection-log.md` header to mutex doc and SHA-67 holder card URL.
4. Cross-link from mutex doc back to inspection log for run history examples.
5. Optionally add SHA-67 to inspection log as infrastructure reference (not a filed finding).

## Files / Areas Likely Affected

- `docs/agent-workflows/daily-project-inspection-log.md`
- `docs/agent-workflows/project-review-mutex.md` (if created by Mid plan)
- Cursor Automation prompt for project review (UI)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: docs render correct relative links; one review run outputs the standardized report block

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] Automation run report format is documented and used.
- [ ] Mutex docs are cross-linked from `daily-project-inspection-log.md`.

## Risks / Open Questions

- Low priority — can ship after High/Mid mutex wiring is verified.
- Report format should align with backlog triage and todo-plan automation reports for operator consistency.
