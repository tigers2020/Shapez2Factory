---
linear_issue: SHA-12
title: reconcile_solver_run leaks ArtifactIngestError to async status poll (HTTP 500)
priority: Low
labels:
  - bug
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Consolidate reconcile error codes documentation (SHA-12 Low)

## Source Issue

- Linear: SHA-12
- Priority: Low

## Scope

Document reconcile failure codes including new ingest-failure path in one place.

## Implementation Plan

1. List all `RECONCILE_FAILURE_*` codes in service module or workflow doc.
2. Cross-link SHA-11 log-fatal code.

## Files / Areas Likely Affected

- TBD — `docs/agent-workflows/` or inline module docstring

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional after High fix.
