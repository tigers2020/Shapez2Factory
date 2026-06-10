---
linear_issue: SHA-64
title: Update perf span tests after runtime compose removal
priority: Low
labels:
  - bug
  - performance
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Update Lab replay compose perf span tests

## Source Issue

- Linear: SHA-64
- Status at planning time: Todo
- Priority: Low

## Problem

`test_lab_replay_compose_perf_spans.py` instruments `artifact_runtime_replay_compose_ms` span from `artifact_runtime_replay_compose.py`. After mid plan removes runtime compose, perf span expectations may fail or reference dead code.

## Scope

- Update or remove perf span assertions tied to deleted runtime compose path.
- Ensure remaining spans (`artifact_manifest_load_ms`, `replay_core_parse_ms`) still covered.

## Non-goals

- Broad perf instrumentation redesign.
- Changing perf_span implementation.

## Implementation Plan

1. Read `test_lab_replay_compose_perf_spans.py` and identify spans tied to runtime compose.
2. Remove `artifact_runtime_replay_compose_ms` expectations or replace with artifact-mapper span if added.
3. Confirm `perf_span` context managers in `artifact_replay_viewer_compose.py` still match test allowlist.
4. Run `pytest tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py`
- `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py -v`
- lint: `ruff check .`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Skip if mid plan already updates perf tests inline.
