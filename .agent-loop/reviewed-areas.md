# Project Review Memory

Tracks areas reviewed by periodic project review automation to prevent duplicate work.

## 2026-06-09 21:21

Reviewed area:
- path/module/feature: `src/shapez2_factory/interfaces/cli/` (`asteroid_solve.py`, exit-code contract, related tests/docs)

Skipped:
- Django subprocess runner (`django_apps/asteroid_lab/services/solver_subprocess_runner.py`) — deferred to future run
- CI workflow (`.github/workflows/ci.yml`) — out of CLI scope this run
- Issues labeled `reviewing` — none present

Findings:
- SHA-7: [docs] CLI exit-code table in artifact design spec contradicts asteroid_solve implementation
- SHA-8: [test] Missing regression coverage for asteroid_solve ExitCode.STACK_UNAVAILABLE (20)

Notes:
- Spec §6 lists exit codes 0/1/2/3/4/5; implementation uses `ExitCode` 0/10/20 per `asteroid_solve.py` and CLI-first checklist.
- `test_cli_exit_codes.py` covers OK and VALIDATION_FAILED only; no `STACK_UNAVAILABLE` assertion in `tests/`.

## 2026-06-09 21:33 (prior run — memory file missing)

Reviewed area:
- `django_apps/asteroid_lab/services/artifact_ingest.py`
- `tests/unit/asteroid_lab/test_artifact_ingest.py`

Skipped:
- memory file did not exist yet; entries reconstructed from Linear backlog

Findings:
- SHA-9: [bug] artifact ingest indexes COMPLETED SolverRun with empty solver_summary when paths/hash validation decoupled
- SHA-10: [test] Missing regression for artifact ingest when manifest.error_code is set

Notes:
- Ingest fail-closed gaps and missing error_code regression coverage.

## 2026-06-09 22:00

Reviewed area:
- `django_apps/asteroid_lab/services/solver_run_reconcile.py`
- `django_apps/web/views/public_pages.py` (async status poll)
- `tests/unit/asteroid_lab/test_reconcile_solver_run.py`

Skipped:
- `artifact_ingest.py` / CLI exit codes (reviewed 2026-06-09; SHA-7–SHA-10)
- issues labeled `reviewing`: none open

Findings:
- SHA-11: [test] Missing regression for reconcile RECONCILE_FAILURE_LOG_FATAL (subprocess log fatal marker)
- SHA-12: [bug] reconcile_solver_run leaks ArtifactIngestError to async status poll (HTTP 500)

Notes:
- `_attempt_artifact_ingest` only catches `ArtifactManifestReadError`; hashed-but-invalid `solver_summary.json` reproduces uncaught `ArtifactIngestError` via pytest.
- `_log_has_fatal_marker` path works manually but has zero repo test coverage.
