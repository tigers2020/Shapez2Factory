---
linear_issue: SHA-64
title: Lab artifact replay compose re-executes L2-L5 solver stack from Django
priority: Low
labels:
  - bug
  - performance
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Perf span test updates after runtime compose removal

## Source Issue

- Linear: SHA-64
- Status at planning time: Todo
- Priority: Low

## Problem

`test_lab_replay_compose_perf_spans.py` may assert spans for `artifact_runtime_replay_compose_ms` and per-layer runtime spans that disappear after Mid plan removes Django L2–L5 re-execution.

## Scope

- Update perf span tests to reflect artifact-only compose path.
- Remove or replace assertions on runtime recompose spans.

## Non-goals

- Changing compose implementation (Mid plan).
- Performance tuning of remaining artifact parse path.

## Implementation Plan

1. After Mid plan merges, run `pytest tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py -v`.
2. Update expected span names: drop `artifact_runtime_replay_compose_ms`, `layer02_ms`–`layer05_ms` if no longer emitted.
3. Retain `artifact_manifest_load_ms`, `replay_core_parse_ms` assertions.
4. Document expected compose latency budget in test docstring.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py`
- `docs/superpowers/reports/2026-06-11-lab-replay-compose-profiling.md` (optional cross-ref)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py -v`
- build: `python manage.py check`
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan (`plans/mid/2026-06-10-SHA-64-artifact-replay-cli-first-compose.md`).
