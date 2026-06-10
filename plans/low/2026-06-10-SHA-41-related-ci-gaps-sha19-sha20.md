---
linear_issue: SHA-41
title: CI never runs scripts/check_governance.ps1 required by AGENTS.md governance acceptance
priority: Low
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Related CI gaps (SHA-19, SHA-20) — tracked separately

## Source Issue

- Linear: SHA-41
- Status at planning time: In Progress
- Priority: Low (deferred items from SHA-41 priority breakdown)

## Problem

SHA-41 scope is governance acceptance only. Related AGENTS.md validation gaps are tracked in separate issues and must not be folded into the governance CI card.

## Scope

Document cross-links only. No implementation in SHA-41.

## Non-goals

- Implementing SHA-19 (`python manage.py check` in CI)
- Implementing SHA-20 (mypy scope `django_apps config src`)
- Fixing pre-existing governance violations

## Implementation Plan

1. When implementing SHA-41, do not add `manage.py check` or expand mypy scope in the same PR.
2. Reference SHA-19 and SHA-20 in PR description if reviewers ask about broader AGENTS.md CI alignment.
3. Implement SHA-19/SHA-20 via their own plan files: `plans/mid/2026-06-10-SHA-19-ci-django-check.md`, `plans/mid/2026-06-10-SHA-20-ci-mypy-scope.md`.

## Files / Areas Likely Affected

- TBD — no files changed under SHA-41 low-priority scope

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Confirm SHA-41 PR diff excludes SHA-19/SHA-20 scope

## Acceptance Criteria

- [ ] Matches the source issue spec (low-priority items remain deferred).
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Reviewers may request bundling CI gaps — resist scope creep; point to SHA-19/SHA-20.
