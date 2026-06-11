# Daily Project Inspection Log

Tracks daily inspection automation runs (target rotation, evidence, filed/skipped findings).

**Related docs:**

- Project review memory: [`.agent-loop/reviewed-areas.md`](../../.agent-loop/reviewed-areas.md)
- Project review mutex / holder card: [`project-review-mutex.md`](./project-review-mutex.md) — lock label `auto:project-review-running` on [SHA-67](https://linear.app/zkaufman/issue/SHA-67/automation-project-review-run-mutex-via-dedicated-linear-holder-card) (infrastructure only)

---

## 2026-06-10 Daily Inspection (earlier run)

**Target:** tests / fixtures / regression coverage (pytest config, validation script portability, gate parity)

**Commands run:**
- `git status`, `git branch -v`, `git log --oneline -15`
- `python3 manage.py check`
- `ruff check .`
- `mypy src`
- `mypy django_apps config src` (963 errors — not CI-gated; see SHA-20)
- `black --check .` (pass on `origin/master`; fail on this branch before `1424a207` ancestry)
- `pytest tests/unit/architecture/ -q`
- `pytest tests/integration/web/test_asteroid_miner_layout_solver_async.py -q`
- `pytest --markers`, `pytest --collect-only` (config source warning)
- `gh run list --workflow=ci.yml --limit 5`, `gh run view 27273247252 --log-failed`
- `gh pr list --limit 5`, review of `origin/master:.agent-loop/reviewed-areas.md`

**Files/areas reviewed:**
- `pytest.ini`, `pyproject.toml` (`[tool.pytest.ini_options]`)
- `tests/conftest.py`, `tests/integration/web/test_asteroid_miner_layout_solver_async.py`
- `scripts/test_fast.ps1`, `scripts/test_full.ps1`, `AGENTS.md` § Validation
- `documents/ai/manuals/testing.md`
- `.github/workflows/ci.yml` (cross-check vs prior SHA-18–SHA-20 filings)
- `origin/master:.agent-loop/reviewed-areas.md` (duplicate prevention)

**Findings filed:**

> **Linear MCP blocked:** `https://mcp.linear.app/mcp` returned 401 in this cloud agent session (no `LINEAR_API_KEY`). Draft cards below were **not** created in Linear; paste into Linear manually or re-run with Linear plugin OAuth.

### Draft — SHA-45 (proposed)

**Title:** `[test] Drop or sync stale pyproject.toml pytest config ignored by pytest.ini`

**Labels:** test, infra, refactor | **Priority:** Low

### Draft — SHA-46 (proposed)

**Title:** `[infra] Add cross-platform fast test gate script; AGENTS.md lists PowerShell-only test_fast.ps1`

**Labels:** infra, test, automation, docs | **Priority:** Medium

**Findings skipped (duplicate or weak):**
- CI gaps SHA-18..SHA-20, SHA-30, SHA-40, SHA-41, SHA-44 (see `.agent-loop/reviewed-areas.md`)
- `black --check` failure on branch ancestry without `1424a207` — not filed

**Duplicate checks:**
- Read `origin/master:.agent-loop/reviewed-areas.md` (SHA-7–SHA-44 backlog)
- Linear MCP search unavailable (401)

**Next recommended target:** core runtime / solver / domain logic (`src/shapez2_factory/application/asteroid_lab/layers/`)

---

## 2026-06-10 Daily Inspection (13:01 UTC cron)

**Target:** core runtime / solver / domain — Django subprocess runner + stack orchestration (`django_apps/asteroid_lab/services/solver_subprocess_runner.py`, `solver_runtime_entry.py`, `src/shapez2_factory/interfaces/cli/asteroid_solve.py`, `stack_runner.py`)

**Commands run:**
- `git status`, `git branch -v`, `git log --oneline -15`
- `python3 manage.py check`
- `ruff check django_apps/asteroid_lab/services/solver_subprocess_runner.py src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `pytest tests/unit/asteroid_lab/layers/ tests/unit/asteroid_lab/test_solver_subprocess_runner.py tests/unit/shapez2_factory/ -q` (352 passed, 1 failed under xdist batch)
- `pytest tests/unit/asteroid_lab/test_solver_subprocess_runner.py -q` (5 passed)
- `pytest tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py::test_retention_prunes_oldest_runs_per_project -n 4` (4/5 failed — mtime flake reproduced)
- `curl https://api.linear.app/graphql` (401 — no API key)

**Files/areas reviewed:**
- `django_apps/asteroid_lab/services/solver_subprocess_runner.py`
- `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- `django_apps/asteroid_lab/services/solver_run_reconcile.py` (async ingest path contrast)
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (`ExitCode`, artifact write before return)
- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` (`_prune_old_runs`)
- `tests/unit/asteroid_lab/test_solver_subprocess_runner.py`
- `tests/unit/asteroid_lab/layers/test_layer_post_summary_log.py`
- `.agent-loop/reviewed-areas.md`, automation memory `daily-inspection.md`

**Findings filed:**

> **Linear MCP blocked:** `https://api.linear.app/graphql` returned 401 (no `LINEAR_API_KEY`). Draft cards below were **not** created in Linear.

### Draft — SHA-47 (proposed)

**Title:** `[bug] Sync run_solver_subprocess aborts before ingest when CLI returns exit 20 with written artifacts`

**Description:**

## Problem
`asteroid_solve run` finalizes artifact directories then returns `ExitCode.STACK_UNAVAILABLE` (20) when `RunStackUseCase` reports `ok=False`. The synchronous Django wrapper `run_solver_subprocess` raises `SolverSubprocessError` on any non-zero return code, so `_run_subprocess_runtime_for_project` never calls `ingest_artifact_for_project`. Artifacts on disk are orphaned; `SolverRun` rows are not created/indexed for partial-failure diagnostics. The async reconcile path ingests from `artifact_dir` regardless of exit code — sync and async behavior diverge.

## Evidence
- `asteroid_solve.py` lines 248–287: `writer.finalize(manifest)` then `return int(ExitCode.OK if result.ok else ExitCode.STACK_UNAVAILABLE)`
- `solver_subprocess_runner.py` lines 192–195: `if completed.returncode != 0: raise SolverSubprocessError(...)`
- `solver_runtime_entry.py` lines 92–118: catch `SolverSubprocessError` → `ok=False` without ingest
- `solver_run_reconcile.py` `_attempt_artifact_ingest`: ingests when manifest validates (async path)
- `tests/unit/asteroid_lab/test_solver_subprocess_runner.py`: no test for exit 20 + artifact present
- Related but distinct: SHA-8 (CLI exit 20 unit test), SHA-10 (ingest `error_code` regression)

## Impact
Blocking sync solver runs (`run_solver_runtime_for_project`) lose artifact-first contract on stack-unavailable outcomes. Lab UI/replay cannot surface partial layer summaries; operators see generic subprocess failure instead of ingested FAILED run with manifest `error_code`.

## Suggested Fix
Treat exit 20 like reconcile: if `artifact_dir` contains a verified manifest, return `SolverSubprocessResult` (do not raise) and let runtime entry ingest; map CLI exit to `SolverRun` FAILED/COMPLETED per manifest `error_code`. Preserve raise for exit 10 (validation) when no artifact dir. Add regression test mirroring SHA-8 fixture with `returncode=20` and asserting ingest proceeds.

## Acceptance Criteria
- Sync subprocess path ingests artifacts when CLI exits 20 and manifest verifies
- `SolverRun` row reflects manifest `error_code` / FAILED status
- Exit 10 without artifacts still raises `SolverSubprocessError`
- Regression test in `tests/unit/asteroid_lab/test_solver_subprocess_runner.py` or runtime entry tests

**Labels:** bug, test, automation | **Priority:** High

---

### Draft — SHA-48 (proposed)

**Title:** `[test] layer_post_summary_log retention prune flakes under pytest-xdist (mtime tie-breaking)`

**Description:**

## Problem
`_prune_old_runs` sorts run directories by `st_mtime` only. When four sessions are created in rapid succession (as in `test_retention_prunes_oldest_runs_per_project`), mtimes often tie; Python's sort is unstable for equal keys, so the wrong directories survive. The test fails intermittently under `pytest -n auto` (observed in layer batch run and 4/5 reproduces with `-n 4`).

## Evidence
- `layer_post_summary_log.py` `_prune_old_runs`: `run_dirs.sort(key=lambda p: p.stat().st_mtime)`
- `test_layer_post_summary_log.py::test_retention_prunes_oldest_runs_per_project` expects `{"run-2", "run-3"}`
- Failure under `-n 4`: `assert {'run-0', 'run-3'} == {'run-2', 'run-3'}`
- Solo run passes; batch `pytest tests/unit/asteroid_lab/layers/` had 1 failure in 352 tests

## Impact
CI / `test_fast.ps1` (`-n auto`) non-determinism; false reds on unrelated PRs; erodes trust in layer observability gate.

## Suggested Fix
Use deterministic tie-breaker (`run_dir.name` or creation order) in sort key, e.g. `sort(key=lambda p: (p.stat().st_mtime, p.name))`. Alternatively touch each run dir with monotonic timestamps in the test setup.

## Acceptance Criteria
- `test_retention_prunes_oldest_runs_per_project` passes 20 consecutive runs with `-n 4`
- Prune semantics unchanged: retain newest `max_runs` directories

**Labels:** test, infra | **Priority:** Medium

**Findings skipped (duplicate or weak):**
- CLI exit 20 test coverage only — **SHA-8** (does not cover Django ingest gap)
- Ingest `manifest.error_code` regression — **SHA-10**
- L3/L5 `LayerBudgetContext` discard — **SHA-14**, **SHA-31**
- L6 `validation_passed` semantics — **SHA-15**
- `budget_ctx` discarded in L2/L3 entrypoints — observed (`_ = budget_ctx`); L2 is fast planning, lower signal than SHA-31
- `spawn_solver_subprocess_detached` direct unit coverage — thin but async path covered via `test_solver_run_async_spawn.py` (mocked); not filed

**Duplicate checks:**
- `.agent-loop/reviewed-areas.md` (SHA-7–SHA-44; subprocess runner deferred 2026-06-09)
- Automation memory `daily-inspection.md` (SHA-45/46 drafts from earlier 2026-06-10 run)
- `plans/` grep: no existing SHA-47/48; SHA-8/10 related but different root cause
- Linear API search unavailable (401)

**Next recommended target:** UI / frontend / interaction flow (Asteroid Lab replay viewer, lazy cache UX) — SHA-37/38 filed; consider `django_apps/web/views/` lab pages or `basedata_import_service.py` (deferred 2026-06-10 02:30)
