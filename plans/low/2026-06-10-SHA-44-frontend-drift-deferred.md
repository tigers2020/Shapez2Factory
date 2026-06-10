---
linear_issue: SHA-44
title: CI never runs build:css; committed app.css can drift from Tailwind source
priority: Low
labels:
  - ui
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Frontend drift deferred items (SHA-44 Low scope)

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Low

## Problem

SHA-44 Low priority section tracks separate frontend bundle drift gates (SHA-35, SHA-40, SHA-42) and existing pytest substring guards for lab CSS classes — out of scope for the `build:css` Mid gate.

## Scope

Track deferred low-priority follow-ups; no implementation in SHA-44 Mid PR.

## Non-goals

- Implementing SHA-35/SHA-40/SHA-42 gates in this card
- Expanding pytest substring guards beyond optional local contract test

## Implementation Plan

1. Confirm SHA-35, SHA-40, SHA-42 own their respective drift gates.
2. Cross-link from SHA-44 Mid plan Risks if not already present.
3. Leave `test_asteroid_lab_ui_strings.py` substring checks as-is unless expanded in a separate card.

## Files / Areas Likely Affected

- TBD (deferred to SHA-35, SHA-40, SHA-42)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: confirm sibling drift cards have plans before closing SHA-44

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Low section items are fully owned by other Linear issues; this plan is tracking-only.
