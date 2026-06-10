---
linear_issue: SHA-40
title: CI never runs recipe graph editor Vitest or build:recipe-graph-editor; committed bundles can drift
priority: Low
labels:
  - automation
  - infra
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Unified frontend static-asset CI pattern (SHA-40 Low)

## Source Issue

- Linear: SHA-40
- Status at planning time: Todo
- Priority: Low

## Problem

Recipe graph editor CI (Mid plan) will add another one-off Node build + diff job. Graph-layout (SHA-35), CSS (SHA-44), and locale (SHA-42) gates share the same structural pattern. A unified frontend static-asset CI workflow reduces duplication and documents one operator path for all committed bundles.

## Scope

- Consolidate recipe-graph and graph-layout CI steps into shared workflow pattern after individual gates land.
- Document cross-links between SHA-35, SHA-40, SHA-44, SHA-42 in validation manuals.

## Non-goals

- Recipe graph editor Vitest/build gate (Mid plan).
- Graph-layout bundle gate (SHA-35 Mid).
- Changing bundle output paths or build scripts.

## Implementation Plan

1. After SHA-40 Mid CI lands, compare workflow steps with SHA-35 graph-layout job in `.github/workflows/ci.yml`.
2. Extract reusable composite action: Node setup → targeted `npm ci` → build script → `git diff --exit-code` on output paths.
3. Parameterize build command and diff paths for `build:recipe-graph-editor` vs `build:graph-layout`.
4. Update `documents/ai/manuals/frontend.md` with unified "committed static assets" section listing all build targets from `structure.md`.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json`
- `documents/ai/manuals/frontend.md`
- `docs/agent-workflows/validation-routine.md`
- TBD — shared GitHub Action or `scripts/check_static_assets.ps1`

## Validation Plan

- lint: N/A unless scripts added
- typecheck: N/A
- tests: verify both recipe-graph and graph-layout CI jobs pass after refactor
- build: run unified local check script on `master` — expect exit 0
- manual verification: Single doc section covers all frontend bundle freshness gates

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on SHA-40 Mid (and ideally SHA-35 Mid) landing first.
- Over-abstraction may obscure per-target failure messages — keep job names explicit in CI UI.
