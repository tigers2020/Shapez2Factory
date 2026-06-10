---
linear_issue: SHA-7
title: CLI exit-code table in artifact design spec contradicts asteroid_solve implementation
priority: Low
labels:
  - docs
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Consolidate exit-code documentation (SHA-7 Low)

## Source Issue

- Linear: SHA-7
- Status at planning time: Todo
- Priority: Low

## Problem

Exit-code documentation is scattered across spec §6, checklist, and CLI tests. Operators may miss the canonical table after Mid-priority alignment work.

## Scope

Optional polish: single canonical exit-code table with links from ADR or agent workflow docs.

## Non-goals

- No runtime or test behavior changes.
- No new exit codes.

## Implementation Plan

1. After Mid plan lands, identify all docs mentioning CLI exit codes.
2. Add a short "CLI exit codes" subsection to one canonical doc (spec §6 or `documents/ai/manuals/` if appropriate).
3. Add cross-links from `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/README.md` and any ADR touching subprocess contracts.
4. Remove duplicate tables or replace with link to canonical section.

## Files / Areas Likely Affected

- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/README.md`
- TBD — other docs found by grep

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Link check; no contradictory exit integers in linked docs

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan completion; defer if Mid not merged.
- Document inventory (`documents/index/document_inventory.md`) may need a one-line update if new canonical location chosen.
