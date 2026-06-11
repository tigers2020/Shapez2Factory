---
linear_issue: SHA-18
title: ci.yml push trigger targets main but repository default branch is master
priority: Mid
labels:
  - automation
  - infra
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Align all workflow branch triggers (SHA-18 Mid)

## Source Issue

- Linear: SHA-18
- Priority: Mid

## Problem

`rttp-lab-macro-smoke.yml` targets `master` while `ci.yml` targeted `main` — inconsistent branch policy across workflows.

## Scope

Audit all `.github/workflows/*.yml` for branch triggers; align with default branch.

## Implementation Plan

1. `rg 'branches:' .github/workflows/`
2. Normalize push/pull_request branch lists.
3. Note any intentional exceptions in workflow comments.

## Files / Areas Likely Affected

- `.github/workflows/*.yml`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Pair with High plan in same PR.
