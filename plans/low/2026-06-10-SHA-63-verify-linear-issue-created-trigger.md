---
linear_issue: SHA-63
title: Verify Cursor Linear issue-created automation trigger (manual UI repro)
priority: Low
labels:
  - automation
  - test
  - priority:low
status: planned
created_by: todo-plan-automation
---

# Plan: Verify Cursor Linear issue-created automation trigger (manual UI repro)

## Source Issue

- Linear: SHA-63
- Status at planning time: Todo
- Priority: Low

## Problem

Confirm that the Cursor Automation `02 Linear Backlog Issue Triage` fires when a new Linear issue is created in the Shapez2Factory team, without requiring ngrok/bridge.

## Scope

- Verify issue-created webhook/trigger reaches Cursor Automation.
- Confirm automation can read the issue and transition it through the triage workflow (labels, spec description, Todo move).
- Document verification result on the Linear issue.

## Non-goals

- Changing automation logic or Linear integration config (unless trigger fails).
- Production code changes in the Shapez2Factory repository.

## Implementation Plan

1. Confirm the repro card (SHA-63) was created in Backlog with ngrok/bridge off (already done per issue spec).
2. Open Cursor Automations → Runs panel and confirm a new run for `02 Linear Backlog Issue Triage` started within ~3 minutes of issue creation.
3. Verify triage outcomes on SHA-63:
   - Structured spec sections present (Problem, Scope, Proposed Approach, Acceptance Criteria).
   - Topic labels applied (`automation`, `test`, `priority:low`).
   - Issue moved from Backlog to Todo.
4. Cross-check related repro cards (SHA-62, SHA-65) only if needed to distinguish trigger paths; do not duplicate work unless a path fails.
5. Document pass/fail evidence in a Linear comment (run ID or timestamp, observed status transitions, labels).
6. Close or cancel SHA-63 after verification is complete, per issue Proposed Approach step 4.

## Files / Areas Likely Affected

- TBD — no repository files expected for a successful trigger verification.
- Cursor Automations configuration (external to repo).
- Linear issue SHA-63 and related trigger-test issues (SHA-62, SHA-65).

## Validation Plan

- lint: N/A (no code changes)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification:
  - Cursor Automations Runs panel shows a run tied to issue-created event for Shapez2Factory.
  - SHA-63 received triage processing (spec, labels, Todo status).
  - Result documented in Linear comment.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Trigger latency may exceed ~3 minutes; document actual delay if observed.
- Multiple concurrent trigger-test cards (SHA-62, SHA-63, SHA-65) may cause ambiguous run attribution — note which issue ID the run references.
- If trigger fails, follow-up work to fix integration is out of scope for this plan unless explicitly opened as a new issue.
