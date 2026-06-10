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

# Plan: Deferred frontend static-asset CI risks (SHA-35 Low)

## Source Issue

- Linear: SHA-35
- Status at planning time: In Progress (triggered from Todo)
- Priority: Low

## Problem

SHA-35 Mid scope covers graph-layout bundle freshness only. Other committed frontend artifacts can still drift without CI gates.

## Scope

Document and track out-of-scope drift risks referenced in the SHA-35 priority breakdown. No implementation in the SHA-35 Mid slice.

## Non-goals

- Implementing recipe graph editor CI (SHA-40).
- Implementing Tailwind `build:css` CI (SHA-44).
- Implementing locale catalog CI (SHA-42).
- Designing a single unified frontend CI job in this slice.

## Implementation Plan

1. **Note SHA-40 in SHA-35 PR description or Mid plan Risks** — recipe graph editor Vitest/build drift is tracked separately.
2. **Defer unified pattern** — a future issue may combine `build:css`, `build:graph-layout`, `build:recipe-graph-editor`, and locale rebuild checks into one Node CI job; not required for SHA-35 acceptance.
3. **Optional follow-up issue** — if operators want one `frontend-freshness` matrix task, file after SHA-35, SHA-44, SHA-40, and SHA-42 land individually.

## Files / Areas Likely Affected

- TBD (docs-only references in SHA-35 PR if desired)
- Related issues: SHA-40, SHA-44, SHA-42

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: confirm SHA-35 Mid PR does not claim coverage of recipe editor or CSS bundles

## Acceptance Criteria

- [ ] Matches the source issue spec (Low items acknowledged, not implemented).
- [ ] Stays within the priority scope (documentation/deferral only).
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Recipe graph editor bundle drift ([SHA-40](https://linear.app/zkaufman/issue/SHA-40)) tracked separately.
- Unified frontend static-asset CI pattern intentionally deferred until individual gates prove stable.
