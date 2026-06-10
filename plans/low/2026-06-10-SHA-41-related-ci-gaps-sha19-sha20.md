---
linear_issue: SHA-41
title: CI never runs scripts/check_governance.ps1 required by AGENTS.md
priority: Low
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Track related CI gaps SHA-19 and SHA-20 separately

## Source Issue

- Linear: SHA-41
- Status at planning time: Todo
- Priority: Low

## Problem

SHA-19 (`manage.py check`) and SHA-20 (mypy scope) are related AGENTS.md CI gaps tracked in separate issues. Issue spec lists them as Low follow-up, not in SHA-41 scope.

## Scope

Cross-reference SHA-19/SHA-20 in governance CI PR; no implementation in this card.

## Non-goals

- SHA-19/SHA-20 fixes.
- Governance check implementation (Mid plan).

## Implementation Plan

1. Add links to SHA-19 and SHA-20 in SHA-41 Linear comment or PR description when Mid plan executes.
2. Optional: single "CI contract alignment" meta-issue if operator wants batching.

## Files / Areas Likely Affected

- TBD (documentation only)

## Validation Plan

- n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Plans for SHA-19/SHA-20 may already exist under `plans/mid/`.
