---
linear_issue: SHA-15
title: RunStackUseCase sets validation_passed from stack success while L6 commit-validate is no-op
priority: Low
labels:
  - bug
  - solver
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Validation pending UI copy polish (SHA-15 Low)

## Source Issue

- Linear: SHA-15
- Priority: Low

## Scope

Update Lab UI copy to show "validation pending" when L6 stub.

## Implementation Plan

1. After Mid semantics fix, update status strings in Lab JS/templates.
2. Manual check in asteroid miner layout lab.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (TBD)
- `django_apps/asteroid_lab/services/solver_run_lab_summary.py`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid contract choice.
