---
linear_issue: SHA-67
title: "[automation] Project review run mutex via dedicated Linear holder card"
priority: Mid
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Wire project-review mutex gate and memory-file contract

## Source Issue

- Linear: SHA-67
- Status at planning time: Todo
- Priority: Mid

## Problem

Label `auto:project-review-running` exists in the Linear workspace but is not wired into the project-review automation prompt/workflow. The holder-card contract (SHA-67 is infrastructure, not a product task) is undocumented. Review runs may skip reading or appending `.agent-loop/reviewed-areas.md`.

## Scope

Document and enforce the full project-review mutex workflow in automation docs/prompt: global gate, per-run label on SHA-67, memory file read/append, and operator-facing holder-card contract.

## Non-goals

- Do not drain or triage Backlog cards from SHA-67.
- Do not change backlog triage mutex (SHA-63 pattern).
- Do not alter review area rotation beyond ensuring memory file is consulted.

## Implementation Plan

1. Add or update `docs/agent-workflows/project-review-mutex.md` (or equivalent section in `daily-project-inspection-log.md`) documenting:
   - SHA-67 is the sole mutex holder for `auto:project-review-running`.
   - Global 45-minute stale-lock window.
   - Run sequence: mutex check → add label to SHA-67 → read memory → review → append memory → remove label in `finally`.
   - SHA-67 must never be triaged or implemented as product work.
2. Update the project-review Cursor Automation prompt to include the mutex steps verbatim (parity with backlog triage `auto:backlog-triage-running` pattern from SHA-63).
3. Require every review run to read `.agent-loop/reviewed-areas.md` before picking an area and append a dated entry after a successful pass (path/module, skipped areas, findings filed, notes).
4. Require review scans to skip issues labeled `reviewing`.
5. Reference parallel pattern: backlog triage uses `auto:backlog-triage-running` on its holder card (SHA-63/65 verification cards).
6. Add a short note in `.agent-loop/reviewed-areas.md` header pointing to the mutex doc and SHA-67 holder role.

## Files / Areas Likely Affected

- `docs/agent-workflows/daily-project-inspection-log.md`
- `docs/agent-workflows/project-review-mutex.md` (new, if split from inspection log)
- `.agent-loop/reviewed-areas.md`
- Cursor Automation prompt for project review (UI)
- Linear labels: `auto:project-review-running`, `reviewing`

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification:
  - Automation prompt includes all mutex steps and memory file requirements
  - Doc describes SHA-67 holder-card contract
  - One review run appends to `.agent-loop/reviewed-areas.md` and consults it on the next run

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] `auto:project-review-running` gate is wired into review automation (parity with backlog triage).
- [ ] Holder-card contract documented so operators know SHA-67 is infrastructure.
- [ ] `.agent-loop/reviewed-areas.md` is consulted before and updated after each successful review pass.

## Risks / Open Questions

- If mutex doc is split vs embedded in `daily-project-inspection-log.md`, avoid duplicate/conflicting instructions.
- Memory file append format should match existing entries in `.agent-loop/reviewed-areas.md` for parseability.
- Backlog triage prompt is not in repo — may need operator to paste parity section from SHA-63 run logs.
