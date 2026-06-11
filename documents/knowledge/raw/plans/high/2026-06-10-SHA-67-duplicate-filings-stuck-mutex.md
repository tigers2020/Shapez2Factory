---
linear_issue: SHA-67
title: "[automation] Project review run mutex via dedicated Linear holder card"
priority: High
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Prevent duplicate review filings and stuck mutex on SHA-67

## Source Issue

- Linear: SHA-67
- Status at planning time: Todo
- Priority: High

## Problem

Concurrent project-review automation runs can overlap and file duplicate SHA-* cards for the same module. If the `auto:project-review-running` label is left on holder card SHA-67 after a failed run, all future review runs block indefinitely.

## Scope

Implement and verify the global mutex gate and `finally` label cleanup so overlapping runs exit with `concurrent-run` and SHA-67 never retains the lock label after a run ends.

## Non-goals

- Do not change review target rotation logic beyond mutex safety.
- Do not implement product/solver fixes filed by review runs.
- Do not modify backlog triage mutex (`auto:backlog-triage-running`).

## Implementation Plan

1. Update the project-review Cursor Automation prompt with hard concurrency rules mirroring backlog triage:
   - Before work: `list_issues` with label `auto:project-review-running` on team Shapez2Factory.
   - For each result, compare `updatedAt` to now; if any issue was updated within 45 minutes, exit immediately with `Status: blocked`, reason `concurrent-run`.
2. Immediately after the gate passes, add label `auto:project-review-running` to SHA-67 only (preserve all existing labels).
3. Wrap the review body in try/finally. In `finally`, always remove `auto:project-review-running` from SHA-67 regardless of success, skip, or failure.
4. On failure before `finally`, add a comment on SHA-67 with the failure reason so operators can diagnose stuck-lock scenarios.
5. During review scans, skip Linear issues labeled `reviewing` (per `.agent-loop/reviewed-areas.md` convention).
6. Set Cursor Automation concurrency to 1 in the UI if exposed.
7. Manual verification: trigger two overlapping runs (or simulate by leaving the label on SHA-67 with recent `updatedAt`) and confirm the second exits `concurrent-run`; confirm label removal after first run completes.

## Files / Areas Likely Affected

- Cursor Automation prompt for periodic project review (UI configuration — not in repo today)
- `docs/agent-workflows/daily-project-inspection-log.md` (mutex contract cross-reference — see Low plan)
- `.agent-loop/reviewed-areas.md` (convention reference for `reviewing` skip)
- Linear workspace labels: `auto:project-review-running`, holder card SHA-67

## Validation Plan

- lint: N/A (automation prompt / docs only)
- typecheck: N/A
- tests: N/A (no product code)
- build: N/A
- manual verification:
  - Second concurrent run within 45 minutes exits `Status: blocked`, reason `concurrent-run`
  - SHA-67 has no `auto:project-review-running` label after run ends (success or failure)
  - Failed run leaves diagnostic comment on SHA-67

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] Review automation exits immediately when another run holds `auto:project-review-running` within 45 minutes.
- [ ] SHA-67 receives the lock label only during an active review run and never retains it after `finally`.

## Risks / Open Questions

- Automation prompt lives in Cursor UI; repo docs must stay in sync or operators will see drift.
- 45-minute stale window is time-based only — a crashed run before `finally` could block until window expires unless manual label removal is documented.
- Dual triggers (Linear status + webhook bridge) caused duplicate runs for SHA-30; ensure only one trigger is enabled for project review.
