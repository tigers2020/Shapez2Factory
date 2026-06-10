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

# Plan: Cross-link frontend bundle drift issues

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Low

## Problem

Related frontend drift gates tracked in SHA-35, SHA-40, SHA-42 separately.

## Scope

Document cross-links; optional unified frontend static-asset CI pattern (future).

## Non-goals

- SHA-35/40/42 implementation.

## Implementation Plan

1. Add cross-references in SHA-44 PR to related bundle drift issues.
2. Optional pytest substring extension in `test_asteroid_lab_ui_strings.py` for local fast feedback.

## Files / Areas Likely Affected

- `documents/ai/manuals/testing.md`
- `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` (optional)

## Validation Plan

- n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Unified CI job deferred per issue non-goals.
