---
linear_issue: SHA-40
title: CI never runs recipe graph editor Vitest or build:recipe-graph-editor; committed bundles can drift
priority: Low
labels:
  - automation
  - infra
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Unified frontend static-asset CI pattern (SHA-40 Low)

## Source Issue

- Linear: SHA-40
- Status at planning time: In Progress (triggered from Todo)
- Priority: Low

## Problem

Frontend static artifacts (graph-layout esbuild bundles, Tailwind `app.css`, locale catalogs, recipe-graph-editor Vite bundles) each have separate drift-class issues. Recipe graph editor CI is addressed in the Mid plan; graph-layout drift remains tracked in [SHA-35](https://linear.app/zkaufman/issue/SHA-35). Operators lack a single documented pattern for “rebuild + git diff” gates across targets.

## Scope

- Document a reusable CI pattern (setup-node → npm ci → target build/test → git diff) for committed static assets.
- Cross-link related issues: SHA-35 (graph-layout), SHA-44 (`build:css`), SHA-42 (locale), SHA-40 (recipe-graph-editor).
- Defer actual consolidation into one umbrella job until individual gates are stable.

## Non-goals

- Implementing graph-layout CI in this card (SHA-35).
- Merging unrelated build targets into one matrix task before each gate is proven.
- Changing any runtime frontend behavior.

## Implementation Plan

1. After Mid plan lands, add a short “Frontend static asset CI gates” subsection to `structure.md` or `docs/agent-workflows/validation-routine.md` listing each target, build command, diff path, and tracking issue.
2. Note shared steps: `actions/setup-node`, root `npm ci`, per-package `npm ci` when nested lockfile exists, rebuild, `git diff --exit-code <path>`.
3. Open or reference a follow-up umbrella issue if consolidating jobs reduces CI minutes without hiding failures.

## Files / Areas Likely Affected

- `structure.md`
- `docs/agent-workflows/validation-routine.md`
- TBD: future umbrella tracking issue

## Validation Plan

- lint: N/A (docs only)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Docs accurately list SHA-35/40/42/44 gates and commands.

## Acceptance Criteria

- [ ] Matches the source issue spec Low priority items.
- [ ] Stays within the priority scope (documentation / cross-link only).
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Unified job may obscure which artifact failed; prefer named matrix tasks until all gates exist.
- Depends on Mid plan completion for recipe-graph-editor gate as reference implementation.
