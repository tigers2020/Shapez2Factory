---
linear_issue: SHA-64
title: Lab artifact replay compose perf span test updates after runtime path removal
priority: Low
labels:
  - bug
  - performance
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Perf span tests after artifact runtime compose removal (SHA-64 follow-up)

## Source Issue

- Linear: SHA-64 (Low priority breakdown)
- Status at planning time: In Progress
- Priority: Low

## Problem

After SHA-64 removes `artifact_runtime_replay_compose.py`, `tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py` will fail because it asserts presence of runtime-only span names (`artifact_runtime_replay_compose_ms`, `replay_compose_l2_reconstruction_ms`, `replay_compose_l3_rim_greedy_ms`, `replay_compose_l4_inner_fill_ms`, `replay_compose_l5_transport_ms`) in deleted or slimmed sources.

## Scope

Update perf span contract tests to reflect artifact-only compose path. Remove references to deleted module and layer re-execution spans; keep manifest/load/parse spans that remain in `artifact_replay_viewer_compose.py`.

## Non-goals

- Changing perf_span instrumentation policy repo-wide.
- Adding new observability spans unless needed for artifact-only path debugging.

## Implementation Plan

1. Run `pytest tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py -v` after Mid plan lands; capture failing assertions.
2. Update `_COMPOSE_CHAIN_SPANS` in `test_lab_replay_compose_perf_spans.py` to drop runtime-only spans tied to deleted `artifact_runtime_replay_compose.py`.
3. Remove `RUNTIME_COMPOSE` from `test_compose_chain_declares_nested_perf_spans` sources tuple if module deleted.
4. Retain spans still declared in `artifact_replay_viewer_compose.py`: `artifact_manifest_load_ms`, `replay_core_parse_ms`, and any timeline payload spans unchanged.
5. Re-run full perf span test file and Lab replay integration tests if present.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py`
- `django_apps/asteroid_lab/services/artifact_replay_viewer_compose.py` (read-only unless span names change)

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py -v`
- build: N/A
- manual verification: Optional — confirm Lab replay GET still logs `replay_cache_miss_compose_ms` without runtime layer spans.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan deleting runtime compose module first; implement immediately after or in same PR if tests block merge.
- Loss of per-layer compose timing may reduce perf diagnostics; acceptable per CLI-first boundary.
