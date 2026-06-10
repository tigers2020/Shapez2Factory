---
linear_issue: SHA-9
title: Artifact ingest indexes COMPLETED SolverRun with empty solver_summary when paths/hash validation decoupled
priority: Low
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Extend required payload key guards beyond solver_summary (SHA-9 Low)

## Source Issue

- Linear: SHA-9
- Status at planning time: Todo
- Priority: Low

## Problem

After Mid fix for `solver_summary`, other declared manifest paths may need the same fail-closed guard.

## Scope

Inventory manifest `paths` keys and extend validation pattern if spec requires.

## Non-goals

- No scope expansion without spec citation.

## Implementation Plan

1. List all keys in artifact design spec §paths.
2. Apply same exist+hash guard to additional required keys if documented.
3. Add tests per key.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/artifact_ingest.py`
- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_artifact_ingest.py -v`
- manual verification: Spec §paths alignment

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Defer until Mid plan lands; may be no-op if only solver_summary is required today.
