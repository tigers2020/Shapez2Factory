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

# Plan: Sync/async ingest alignment for exit-20 stack-failure artifacts

## Source Issue

- Linear: SHA-33 (Mid priority breakdown item)
- Related: SHA-45 (sync `run_solver_subprocess` rejects exit 20 before ingest)
- Status at planning time: In Progress
- Priority: Mid

## Problem

Related ingest mapping inconsistencies with SHA-45 sync path: the async reconcile path ingests stack-failure artifacts from disk regardless of subprocess exit code, but the sync `run_solver_subprocess` raises on any non-zero return code before `ingest_artifact_for_project` runs. Even after SHA-33 fixes manifest `error_code` and ingest FAILED indexing, sync callers (`manage.py run_solver`, sync HTTP when async disabled) may still never reach ingest for exit-20 artifacts.

## Scope

- Document cross-issue dependency: SHA-33 high plan fixes manifest + ingest status; this mid slice tracks sync-path alignment needed for full contract.
- When implementing SHA-45 (or as follow-up in same PR if explicitly scoped), ensure exit `STACK_UNAVAILABLE` (20) with valid `ARTIFACT_WRITTEN` manifest proceeds to ingest.
- Verify ingest result surfaces FAILED status from manifest/`solver_summary` after SHA-33 high plan lands.

## Non-goals

- Rewriting CLI exit-code taxonomy (SHA-7).
- Changing async reconcile behavior (already artifact-first per PR-CLI-7).
- Implementing SHA-45 in full unless explicitly merged into SHA-33 execution scope.

## Implementation Plan

1. **Read sync subprocess contract**
   - `django_apps/asteroid_lab/services/solver_subprocess_runner.py`: `run_solver_subprocess` raises on `returncode != 0`.
   - `django_apps/asteroid_lab/services/solver_runtime_entry.py`: `_run_subprocess_runtime_for_project` only ingests after successful subprocess return.

2. **Define allowlist for artifact-bearing exit codes**
   - Whitelist `ExitCode.STACK_UNAVAILABLE` (20) when `artifact_dir/manifest.json` exists and passes `read_verified_artifact_manifest`.
   - Still fail closed on `VALIDATION_FAILED` (10) and unexpected codes without valid manifest.

3. **Adjust sync runtime entry**
   - After subprocess with exit 20 + valid artifact: call `ingest_artifact_for_project` (same as async reconcile).
   - Return `SolverRuntimeEntryResult` with `ok=False` but populated `solver_run_id` and FAILED-indexed run (post SHA-33 ingest fix).

4. **Regression test**
   - Extend `tests/unit/asteroid_lab/test_solver_subprocess_runner.py`:
     - Mock `run_subprocess_with_tee` returncode 20.
     - Provide artifact dir fixture with manifest + `error_code` set (depends on SHA-33 high plan).
     - Assert ingest attempted and SolverRun created with FAILED status.

5. **Cross-verify with SHA-8 CLI exit test**
   - SHA-8 covers CLI exit 20 assertion; this test covers Django sync ingest path.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_subprocess_runner.py`
- `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- `tests/unit/asteroid_lab/test_solver_subprocess_runner.py`
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md` (reference)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/solver_subprocess_runner.py django_apps/asteroid_lab/services/solver_runtime_entry.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_solver_subprocess_runner.py -v`
- build: N/A
- manual verification: `python manage.py run_solver --slug <slug>` with stack-failure fixture; confirm SolverRun row exists with FAILED status

## Acceptance Criteria

- [ ] Matches the source issue spec (mid breakdown: sync ingest alignment).
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-45 is the canonical issue for sync subprocess allowlist — implement there or coordinate to avoid duplicate PRs.
- Depends on SHA-33 high plan: ingest must mark FAILED when `error_code` or `run_success: false`; otherwise sync ingest would still show COMPLETED.
- Module boundary: Django adapter cannot import CLI `ExitCode` IntEnum directly — use shared constant string or thin port module.
