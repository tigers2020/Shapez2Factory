---
linear_issue: SHA-65
title: Verify post-link Linear issue-created automation trigger
priority: Low
labels:
  - automation
  - priority:low
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Verify post-link Linear issue-created automation trigger

## Source Issue

- Linear: SHA-65
- Status at planning time: Todo
- Priority: Low

## Problem

Confirm that after linking Cursor and Linear accounts, the Cursor Automation `02 Linear Backlog Issue Triage` runs when a new issue card is created in Backlog.

## Scope

- Verify post-link issue-created trigger fires Cursor Automation within ~3 minutes.
- Confirm triage workflow processes the card (spec enrichment, labels, Todo transition).
- Record pass/fail evidence on the Linear card and related repro issues (SHA-63).

## Non-goals

- Modifying integration credentials or automation config unless trigger fails.
- Production code changes in the Shapez2Factory repository.
- Implementing new automation workflows.

## Implementation Plan

1. Confirm Cursor ↔ Linear accounts remain linked at [cursor.com/linear](https://cursor.com/linear).
2. Review Cursor Automations → Runs for an entry tied to this card (SHA-65) within ~3 minutes of Backlog creation.
3. Verify triage output on SHA-65: structured spec sections, priority label, topic labels, and Backlog → Todo transition per triage workflow.
4. Cross-check SHA-63 (manual UI repro) for consistent trigger behavior without ngrok/bridge.
5. Document outcome: mark Done/Canceled with comment summarizing observed run id, timestamp, and whether triage completed; link to SHA-63 if behaviors diverge.

## Files / Areas Likely Affected

- TBD — no repository code changes expected.
- Cursor Automations configuration (external).
- Linear issue SHA-65 / SHA-63 comments (evidence only).

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Cursor Automations run log shows triage entry for SHA-65; Linear card shows triage labels/spec within expected window.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Trigger latency may exceed 3 minutes under load; document actual observed delay.
- If trigger fails post-link, may require Cursor support or credential re-link — out of scope unless repro confirms failure.
- SHA-65 was moved Todo → Canceled → Todo during testing; state history may affect trigger interpretation.
