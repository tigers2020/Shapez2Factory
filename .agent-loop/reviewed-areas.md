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
