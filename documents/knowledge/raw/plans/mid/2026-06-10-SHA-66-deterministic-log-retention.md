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

`create_layer_post_summary_log_session` prunes sibling run directories via `_prune_old_runs`, which orders folders by filesystem `st_mtime` only. When multiple runs are created within the same second (common in unit tests and possible during fast solver batches), tie-breaking is undefined and the wrong directories can be deleted. With `ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_MAX_RUNS=2`, creating `run-0`..`run-3` leaves `{'run-0', 'run-3'}` instead of the expected `{'run-2', 'run-3'}`. The retention unit test fails consistently on `master`.

## Scope

Make layer post-summary run retention deterministic and align the retention unit test with the intended contract. Fix the failing `test_retention_prunes_oldest_runs_per_project` test and eliminate non-deterministic pruning under equal mtimes.

## Non-goals

- Changing the default `ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_MAX_RUNS` value
- Broader observability schema or manifest format changes (unless a minimal `created_at` field is the chosen tie-break)
- Rewriting unrelated layer post-summary writers

## Implementation Plan

1. **Reproduce and confirm failure**
   - Run: `python3 -m pytest tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py::test_retention_prunes_oldest_runs_per_project -q`
   - Expected before fix: FAIL — surviving dirs are `{'run-0', 'run-3'}` instead of `{'run-2', 'run-3'}`.

2. **Choose minimal deterministic sort key in `_prune_old_runs`**
   - Preferred: lexicographic tie-break on directory name after mtime:
     ```python
     run_dirs.sort(key=lambda p: (p.stat().st_mtime, p.name))
     ```
   - Rationale: one-line change; fixes `run-N` test pattern and auto-generated `layer-stack-YYYYMMDD-HHMMSS-*` names when mtimes collide. No manifest schema change required.
   - Alternative (only if name tie-break is insufficient): manifest `created_at` at session `close()` with `(mtime, name)` fallback — higher scope; defer unless review rejects name tie-break.

3. **Apply fix in `layer_post_summary_log.py`**
   - Modify `_prune_old_runs` at line ~98: replace mtime-only sort with `(st_mtime, p.name)` tuple key.
   - Confirm pruning still runs before new directory creation in `create_layer_post_summary_log_session` (~line 230) and never deletes the run currently being opened.

4. **Strengthen unit test contract**
   - Keep `test_retention_prunes_oldest_runs_per_project` assertion: `names == {"run-2", "run-3"}`.
   - Add a test that forces equal mtimes (e.g., `unittest.mock.patch` on `Path.stat` returning identical `st_mtime` for all dirs, or `os.utime` after creating dirs) to lock tie-break behavior independent of filesystem timing.
   - Example equal-mtime test sketch:
     ```python
     def test_retention_tiebreaks_by_name_when_mtime_equal(tmp_path, monkeypatch):
         # create run-0..run-3 dirs with patched equal st_mtime
         # call _prune_old_runs directly or via create_layer_post_summary_log_session
         # assert run-2 and run-3 survive
     ```

5. **Run full module tests including xdist**
   - `python3 -m pytest tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py -q`
   - `python3 -m pytest tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py::test_retention_prunes_oldest_runs_per_project -n 4` (repeat or loop 20× if flake suspected)

6. **Run canonical validation gates**
   - `python manage.py check`
   - `ruff check django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py`
   - `mypy django_apps config src` (scoped if full run is slow)

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` (`_prune_old_runs`, `create_layer_post_summary_log_session`)
- `tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py` (`test_retention_prunes_oldest_runs_per_project`, new equal-mtime test)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py`
- typecheck: `mypy django_apps config src`
- tests: `python3 -m pytest tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py -q`
- build: `python manage.py check`
- manual verification: confirm `var/` retention under rapid session creation keeps newest `max_runs` dirs by creation order (name tie-break when mtimes equal)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] `test_retention_prunes_oldest_runs_per_project` passes consistently (including under `-n 4`).
- [ ] Retention deletes oldest runs by creation order and keeps newest `max_runs` directories deterministically.

## Risks / Open Questions

- Lexicographic name tie-break assumes run directory names are monotonic with creation order (`run-0` < `run-1` < …; `layer-stack-YYYYMMDD-HHMMSS-*` sorts by timestamp prefix). If callers supply non-monotonic custom `run_id` values with equal mtimes, retention order follows name sort — document in Low-priority plan.
- `layer-stack-*` names with identical timestamp prefix and equal mtimes fall back to hex suffix sort; collision probability is negligible.
- Related but out of scope: SHA-36 (L1 observability gap).
