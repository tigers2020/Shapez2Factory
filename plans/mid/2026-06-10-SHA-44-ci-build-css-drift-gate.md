---
linear_issue: SHA-44
title: CI never runs build:css; committed app.css can drift from Tailwind source
priority: Mid
labels:
  - ui
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: CI gate for Tailwind app.css freshness

## Source Issue

- Linear: SHA-44
- Status at planning time: Todo
- Priority: Mid

## Problem

GitHub Actions never runs `npm run build:css`. Committed `django_apps/web/static/web/css/app.css` can drift from `assets/css/input.css` and template `@source` scans.

## Scope

Add CI gate: `npm ci`, `npm run build:css`, fail on dirty `app.css` diff.

## Non-goals

- Tailwind token/styling changes.
- Umbrella job with SHA-35/40/42.
- Editing `auth-layout.css`.

## Implementation Plan

1. Add `build-css-check` matrix task in `.github/workflows/ci.yml`.
2. Run `npm ci`, `npm run build:css`, `git diff --exit-code django_apps/web/static/web/css/app.css`.
3. Update `DESIGN.md` / `structure.md` if operators need visibility.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json`
- `assets/css/input.css`
- `DESIGN.md`

## Validation Plan

- build: CI job on PR
- manual verification: template class change without rebuild fails CI

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Node version pin must match local Tailwind CLI.
