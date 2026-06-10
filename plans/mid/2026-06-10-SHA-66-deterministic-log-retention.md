---
linear_issue: SHA-66
title: Layer post-summary log retention is non-deterministic (mtime-only sort prunes wrong runs)
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Deterministic layer post-summary log retention

## Source Issue

- Linear: SHA-66
- Status at planning time: Todo
- Priority: Mid

## Problem

`create_layer_post_summary_log_session` prunes sibling run directories via `_prune_old_runs`, which orders folders by filesystem `st_mtime` only. When multiple runs are created within the same second (common in unit tests and possible during fast solver batches), tie-breaking is undefined and the wrong directories can be deleted. The retention unit test fails consistently on `master`.

Observed: with `ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_MAX_RUNS=2`, creating `run-0`..`run-3` leaves `{'run-0', 'run-3'}` instead of the expected `{'run-2', 'run-3'}`.

## Scope

Make layer post-summary run retention deterministic and align the retention unit test with the intended contract.

## Non-goals

- Changing the default `ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_MAX_RUNS` value
- Broader observability schema or manifest format changes (unless a minimal `created_at` field is the chosen tie-break)
- Rewriting unrelated layer post-summary writers

## Implementation Plan

1. **Reproduce failure** — run `python3 -m pytest tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py::test_retention_prunes_oldest_runs_per_project -q` and confirm red on `master`.

2. **Choose minimal deterministic sort key** — prefer lexicographic tie-break in `_prune_old_runs`:
   ```python
   run_dirs.sort(key=lambda p: (p.stat().st_mtime, p.name))
   ```
   Rationale: fixes `run-N` test pattern and auto-generated `layer-stack-YYYYMMDD-HHMMSS-*` names when mtimes collide; no manifest schema change.

3. **Apply fix** — edit `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` line 98 in `_prune_old_runs`; keep pruning fail-safe (runs before new directory is created; never delete the run currently being opened).

4. **Add equal-mtime regression test** — extend `tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py`:
   - Option A: patch `Path.stat` to return identical `st_mtime` for all run dirs.
   - Option B: add `test_retention_tiebreaks_by_name_when_mtime_equal` that forces equal mtimes and asserts `run-2`/`run-3` survive.
   Lock contract: oldest by `(mtime, name)` are pruned; newest `max_runs` kept.

5. **Validate** — run full module tests:
   ```bash
   python3 -m pytest tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py -q
   ```
   If CI uses xdist, also run:
   ```bash
   python3 -m pytest tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py::test_retention_prunes_oldest_runs_per_project -n 4 -q
   ```
   Target: 20 consecutive passes with `-n 4` (per `daily-project-inspection-log.md`).

6. **Commit** — single-purpose commit on feature branch.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` (`_prune_old_runs`, `create_layer_post_summary_log_session`)
- `tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py` (`test_retention_prunes_oldest_runs_per_project`, new tie-break test)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py`
- typecheck: `mypy django_apps config src` (scoped files if full gate is heavy)
- tests: `python3 -m pytest tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py -q`
- build: `python manage.py check`
- manual verification: none required (unit tests cover contract)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Lexicographic name tie-break assumes monotonic naming (`run-N`, `layer-stack-*` timestamp prefix). If future run IDs are not lex-orderable with creation order, consider manifest `created_at` fallback (out of scope unless reproved insufficient).
- xdist flake may persist if test relies on real mtimes without explicit equal-mtime assertion; new tie-break test mitigates.
- Pruning still uses mtime as primary key; clock skew across hosts is not addressed (observability-only, acceptable).
