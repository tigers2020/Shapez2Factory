---
linear_issue: SHA-33
title: Stack-failure artifacts write manifest.error_code=null; Django ingest indexes COMPLETED
priority: Mid
labels:
  - bug
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Align sync subprocess exit-20 handling with ingest (SHA-33 Mid)

## Source Issue

- Linear: SHA-33
- Status at planning time: Todo
- Priority: Mid

## Problem

Related ingest mapping inconsistencies with SHA-45: sync `run_solver_subprocess` may reject exit 20 before artifact ingest while async path ingests stack-failure artifacts as COMPLETED.

## Scope

Coordinate sync subprocess runner behavior with High-priority manifest/ingest fix so exit-20 artifacts are handled consistently across sync and async paths.

## Non-goals

- Redesigning async job queue architecture.
- Changing CLI exit code values.

## Implementation Plan

1. After High plan lands, read SHA-45 and `django_apps/asteroid_lab/services/solver_subprocess_runner.py` sync vs async ingest branches.
2. Ensure sync path does not reject exit 20 before ingest when artifact is valid but indicates stack failure.
3. Align status mapping: both paths should index FAILED when manifest/summary indicate failure.
4. Add or extend regression test covering sync subprocess exit-20 → ingest → FAILED status.
5. Cross-link SHA-45 in commit message if same PR or follow-up.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_subprocess_runner.py`
- `tests/unit/asteroid_lab/` (subprocess runner tests — TBD)
- Related: SHA-45

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/`
- typecheck: `mypy django_apps config src`
- tests: sync subprocess + ingest integration tests
- build: N/A
- manual verification: Sync and async paths produce same lifecycle for exit-20 artifacts

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High plan; may merge with SHA-45 if same root cause.
- Sync reject-before-ingest may be intentional guard — verify contract before changing.
