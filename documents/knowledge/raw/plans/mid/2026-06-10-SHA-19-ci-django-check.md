---
linear_issue: SHA-19
title: CI workflow omits python manage.py check required by AGENTS.md validation canon
priority: Mid
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Add python manage.py check to CI workflow

## Source Issue

- Linear: SHA-19
- Status at planning time: Todo
- Priority: Mid

## Problem

`AGENTS.md` requires `python manage.py check` but `ci.yml` never runs Django system checks.

## Scope

Add matrix job or pre-test step running `python manage.py check`.

## Non-goals

- Do not change Django settings beyond CI wiring needs.

## Implementation Plan

1. Read `ci.yml` matrix structure.
2. Add `django-check` task or prepend to test job: `python manage.py check`.
3. Ensure Python/Django deps match existing CI setup.
4. Update `docs/agent-workflows/validation-routine.md` if CI matrix listed there.
5. Verify locally: `python manage.py check`.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `AGENTS.md` (reference)
- `docs/agent-workflows/validation-routine.md`
- `manage.py`
- `config/settings/`

## Validation Plan

- manual verification: `python manage.py check` locally
- CI: workflow runs on PR

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- CI env may need env vars for Django — follow existing test job pattern.
