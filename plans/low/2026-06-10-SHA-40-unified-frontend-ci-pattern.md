---
linear_issue: SHA-40
title: Unified frontend static-asset CI pattern (deferred)
priority: Low
labels:
  - automation
  - infra
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Unified frontend static-asset CI pattern (deferred)

## Source Issue

- Linear: SHA-40
- Status at planning time: In Progress
- Priority: Low (from issue Priority Breakdown)

## Problem

Recipe graph editor CI gating (SHA-40 mid scope) addresses one static-asset drift class. Similar gaps remain for graph-layout bundles (SHA-35), Tailwind `app.css` (SHA-44), and locale catalogs (SHA-42). There is no shared CI pattern or documentation tying these gates together.

## Scope

- Document cross-links between related frontend drift issues after SHA-40 mid work lands.
- Optionally sketch a future unified `frontend-static-assets` CI job pattern (design note only — no implementation in this card).

## Non-goals

- Implementing SHA-35 graph-layout CI in this card.
- Implementing SHA-44 `build:css` or SHA-42 locale gates.
- Changing recipe graph editor runtime behavior.
- Merging unrelated build targets into one umbrella job before individual cards are resolved.

## Implementation Plan

1. After SHA-40 mid CI lands, add a short "Frontend static asset CI" subsection to `documents/ai/manuals/testing.md` or `structure.md` listing each gate, its command, and its Linear issue (SHA-40, SHA-35, SHA-44, SHA-42).
2. In SHA-40 PR description, cross-link SHA-35 for graph-layout drift.
3. Optionally open or update a tracking note (Linear comment or doc) describing a future unified job structure: single Node setup, parallel sub-steps per asset class, independent `git diff` checks per output directory.
4. Defer any code consolidation until SHA-35 / SHA-44 / SHA-42 mid cards are individually planned and implemented.

## Files / Areas Likely Affected

- `documents/ai/manuals/testing.md`
- `structure.md`
- TBD: future `.github/workflows/ci.yml` refactor (not in SHA-40 scope)

## Validation Plan

- lint: N/A (docs-only)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: confirm doc cross-links resolve and list correct npm commands per asset class

## Acceptance Criteria

- [ ] SHA-35, SHA-44, SHA-42 remain tracked separately with visible cross-links from SHA-40 docs/PR.
- [ ] No unrelated behavior is changed.
- [ ] Unified CI pattern is documented as deferred future work, not silently assumed done.
- [ ] Matches the source issue spec low-priority items.
- [ ] Stays within the priority scope.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Premature unification could couple unrelated build failures; keep jobs independent until all asset classes have working gates.
- SHA-35 may need esbuild-only setup while recipe-graph needs Vite — unified job must not over-share install steps incorrectly.
