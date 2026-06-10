---
linear_issue: SHA-40
title: CI never runs recipe graph editor Vitest or build:recipe-graph-editor
priority: Low
labels:
  - automation
  - infra
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Unified frontend static-asset CI pattern (SHA-35 cross-link)

## Source Issue

- Linear: SHA-40
- Status at planning time: Todo
- Priority: Low

## Problem

SHA-35 tracks graph-layout bundle drift separately. Issue spec requests cross-linking for a future unified frontend static-asset CI pattern.

## Scope

Document shared CI pattern for recipe-graph and graph-layout bundle gates without implementing SHA-35 in this card.

## Non-goals

- SHA-35 graph-layout implementation.
- Recipe graph Vitest/build gate (Mid plan).

## Implementation Plan

1. Add comment or short doc section in `ci.yml` or `documents/ai/manuals/testing.md` describing reusable Node CI template.
2. Link SHA-35 and SHA-40 in both issues for follow-up consolidation.

## Files / Areas Likely Affected

- `documents/ai/manuals/testing.md`
- `.github/workflows/ci.yml` (comment only)

## Validation Plan

- n/a (docs/planning)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Consolidation may wait until both SHA-35 and SHA-40 Mid plans land.
