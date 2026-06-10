---
linear_issue: SHA-18
title: ci.yml push trigger targets main but repository default branch is master
priority: High
labels:
  - automation
  - infra
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Fix ci.yml push trigger for default branch master

## Source Issue

- Linear: SHA-18
- Status at planning time: Todo
- Priority: High

## Problem

`.github/workflows/ci.yml` runs on push to `main` only; repository default branch is `master`. Direct pushes/merges to `master` skip CI gates.

## Scope

Update `ci.yml` push branches to include `master` (or replace `main` with `master` per team policy).

## Non-goals

- Do not rename default branch in this issue unless spec requires.

## Implementation Plan

1. Open `.github/workflows/ci.yml` lines 5–7.
2. Add `master` to `push.branches` (or set to `master` only if `main` unused).
3. Verify alignment with `rttp-lab-macro-smoke.yml` which already targets `master`.
4. Push test branch or use workflow_dispatch to confirm trigger (if available).
5. Document in PR description.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `.github/workflows/rttp-lab-macro-smoke.yml` (consistency check)
- `AGENTS.md` (reference only)

## Validation Plan

- lint: N/A
- tests: N/A (workflow change)
- manual verification: Confirm `on.push.branches` includes `master`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- If team migrates to `main` later, dual-branch trigger may be intentional short-term.
