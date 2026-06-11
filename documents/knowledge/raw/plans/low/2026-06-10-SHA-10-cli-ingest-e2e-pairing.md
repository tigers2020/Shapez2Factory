---
linear_issue: SHA-10
title: Missing regression for artifact ingest when manifest.error_code is set
priority: Low
labels:
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Optional CLI ingest E2E pairing (SHA-10 Low)

## Source Issue

- Linear: SHA-10
- Priority: Low

## Problem

Unit test alone may miss subprocess→ingest integration for error artifacts.

## Scope

Optional integration test pairing SHA-8 CLI exit with ingest FAILED indexing.

## Implementation Plan

1. After SHA-8 and SHA-10 Mid tests land, evaluate need for integration test.
2. Add only if gap remains.

## Files / Areas Likely Affected

- TBD integration test path under `tests/integration/`

## Validation Plan

- tests: targeted pytest if added

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional; may defer.
