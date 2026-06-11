---
linear_issue: SHA-33
title: Stack-failure artifacts write manifest.error_code=null; Django ingest indexes COMPLETED
priority: Low
labels:
  - bug
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Document manifest.error_code for stack failures (SHA-33 Low)

## Source Issue

- Linear: SHA-33
- Status at planning time: Todo
- Priority: Low

## Problem

Manifest schema documentation may not describe when `error_code` is set on stack-failure artifacts vs successful runs.

## Scope

Manifest schema documentation updates after High-priority fix.

## Non-goals

- No runtime behavior changes.
- No exit code enum changes.

## Implementation Plan

1. After High plan lands, update artifact design spec manifest section with `error_code` population rules for stack failures.
2. Add cross-link from `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/checklist.md` if checklist references manifest fields.
3. Grep docs for stale "null error_code means success" wording and correct.

## Files / Areas Likely Affected

- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/checklist.md`

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Spec § manifest describes error_code for failed stack runs

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Coordinate with SHA-7 exit-code doc alignment to avoid contradictory tables.
- Depends on High plan defining actual error_code values written.
