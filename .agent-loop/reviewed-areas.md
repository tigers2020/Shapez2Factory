# Project Review Memory

Tracks incremental review areas and created Linear issues to prevent duplicate work.

## 2026-06-09 21:21 (prior run — memory file missing)

Reviewed area:
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py`
- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`

Skipped:
- memory file did not exist yet; entries reconstructed from Linear backlog

Findings:
- SHA-7: [docs] CLI exit-code table in artifact design spec contradicts asteroid_solve implementation
- SHA-8: [test] Missing regression coverage for asteroid_solve ExitCode.STACK_UNAVAILABLE (20)

Notes:
- Prior automation run created issues before review memory was initialized.

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
