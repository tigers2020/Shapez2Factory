---
linear_issue: SHA-35
title: CI never runs build:graph-layout; committed graph layout bundles can drift from TypeScript source
priority: Low
labels:
  - automation
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Deferred unified frontend static-asset CI pattern

## Source Issue

- Linear: SHA-35
- Status at planning time: In Progress
- Priority: Low (deferred items from SHA-35 priority breakdown)

## Problem

Several committed frontend artifacts (graph layout JS, Tailwind CSS, recipe graph editor bundle, locale catalogs) each require manual regeneration. SHA-35 addresses graph-layout only. A unified CI pattern could reduce duplicated npm/git-diff jobs.

## Scope

Document and track only — no implementation in SHA-35. Capture cross-issue dependencies for a future consolidation slice.

## Non-goals

- Implementing SHA-40 (recipe graph editor Vitest/build gate).
- Implementing SHA-44 (build:css freshness).
- Implementing SHA-42 (locale catalog freshness).
- Changing graph-layout CI gate delivered in the mid-priority plan.

## Implementation Plan

1. After SHA-35 mid plan lands, note related Linear issues in a short comment or ADR stub if the team wants a meta-tracking doc.
2. When scheduling consolidation, design one reusable workflow fragment: `npm ci` → targeted build script → `git diff --exit-code <paths>`.
3. Defer until at least two gates exist (SHA-35 + one of SHA-40/SHA-44/SHA-42) to validate the pattern.

## Files / Areas Likely Affected

- TBD — future `.github/workflows/ci.yml` refactor only
- Related issues: SHA-40, SHA-44, SHA-42

## Validation Plan

- lint: N/A (docs/tracking only)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: confirm SHA-35 graph-layout gate passes before starting consolidation

## Acceptance Criteria

- [ ] Remaining risks from SHA-35 spec are reported (recipe graph editor drift tracked in SHA-40).
- [ ] Unified pattern explicitly deferred, not silently dropped.
- [ ] No unrelated behavior is changed by this tracking plan.

## Risks / Open Questions

- Premature abstraction may fight per-asset build tooling differences (esbuild vs Tailwind vs Vite).
- Consolidation should not block SHA-35 mid delivery.
