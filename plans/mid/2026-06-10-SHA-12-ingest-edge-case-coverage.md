---
linear_issue: SHA-12
title: reconcile_solver_run leaks ArtifactIngestError to async status poll (HTTP 500)
priority: Mid
labels:
  - bug
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Mid-priority ingest edge cases for reconcile (SHA-12)

## Source Issue

- Linear: SHA-12
- Priority: Mid

## Problem

Valid hashes + invalid JSON payload edge cases beyond primary repro may still leak if not covered.

## Scope

Expand regression tests for hashed-but-unparseable payloads after High fix.

## Implementation Plan

1. After High plan lands, enumerate ingest failure modes that produce `ArtifactIngestError`.
2. Add parameterized unit tests for each mode in reconcile context.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_reconcile_solver_run.py`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High plan.
