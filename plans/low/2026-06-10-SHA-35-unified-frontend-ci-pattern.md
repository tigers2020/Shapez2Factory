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

# Plan: Unified frontend static-asset CI pattern (SHA-35 Low)

## Source Issue

- Linear: SHA-35
- Status at planning time: Todo
- Priority: Low

## Problem

Graph-layout bundle freshness (Mid plan) will add a one-off CI job. Similar drift risks exist for recipe graph editor (SHA-40), Tailwind CSS (SHA-44), and locale builds (SHA-42). A unified frontend static-asset CI pattern would reduce duplicated workflow steps and operator confusion.

## Scope

- Design a reusable CI pattern for Node install → build → git-diff freshness checks across frontend static bundles.
- Document operator workflow in frontend/validation manuals.

## Non-goals

- Implementing SHA-40 / SHA-44 / SHA-42 gates in this plan.
- Changing any bundle build scripts or output paths.
- Rewriting graph layout or recipe editor source.

## Implementation Plan

1. After Mid graph-layout CI lands, extract common steps from `.github/workflows/ci.yml` into a reusable composite action or shared workflow snippet (install Node, `npm ci`, build target, diff check).
2. Map all static bundle targets: `build:graph-layout` → `django_apps/web/static/web/js/solver_graph_layout.js`, `editor_graph_layout.js`; cross-link SHA-40 `build:recipe-graph-editor` output path.
3. Update `documents/ai/manuals/frontend.md` with a single "static asset freshness" section referencing canonical build commands.
4. Optionally add a local helper script under `scripts/` mirroring CI diff checks for developer pre-push use.

## Files / Areas Likely Affected

- `.github/workflows/ci.yml`
- `package.json`
- `documents/ai/manuals/frontend.md`
- `docs/agent-workflows/validation-routine.md`
- TBD — `.github/actions/frontend-freshness/` or `scripts/check_frontend_bundles.ps1`

## Validation Plan

- lint: N/A unless scripts added
- typecheck: N/A
- tests: verify existing graph-layout CI job still passes after refactor
- build: run unified local script against current `master` — expect exit 0
- manual verification: contributor docs show one pattern for all frontend bundle gates

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan (graph-layout CI) landing first.
- Different packages may need distinct `npm ci` roots (`frontend/recipe_graph_editor/` vs root) — pattern must accommodate both.
