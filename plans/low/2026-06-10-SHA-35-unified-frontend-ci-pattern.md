---
linear_issue: SHA-35
title: Unified frontend static-asset CI pattern (deferred)
priority: Low
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Unified frontend static-asset CI freshness pattern

## Source Issue

- Linear: SHA-35
- Status at planning time: Todo
- Priority: Low

## Problem

Graph-layout, CSS (SHA-44), locale (SHA-42), and recipe-graph-editor (SHA-40) each need separate freshness gates. A shared CI pattern reduces duplication.

## Scope

- Document or script a reusable `rebuild-and-diff` CI step template.
- Optional: single `frontend-freshness` job running multiple build targets.

## Non-goals

- Implementing SHA-40/42/44 in this plan.

## Implementation Plan

1. After SHA-35 mid plan lands, extract CI snippet to `scripts/ci_check_static_bundles.sh` or docs example.
2. Cross-link SHA-40, SHA-42, SHA-44 for future adoption.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `docs/agent-workflows/validation-routine.md` (optional)

## Validation Plan

- manual: CI snippet reusable for second bundle target

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Deferred items documented.

## Risks / Open Questions

- Defer until at least two freshness gates exist to avoid premature abstraction.
