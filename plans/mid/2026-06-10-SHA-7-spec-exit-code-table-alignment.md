---
linear_issue: SHA-7
title: CLI exit-code table in artifact design spec contradicts asteroid_solve implementation
priority: Mid
labels:
  - docs
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: CLI exit-code table in artifact design spec contradicts asteroid_solve implementation

## Source Issue

- Linear: SHA-7
- Status at planning time: Todo
- Priority: Mid

## Problem

The canonical artifact design spec documents CLI subprocess exit codes (0, 1, 2, 3, 4, 5) that do not match the implemented `ExitCode` enum in `asteroid_solve.py` (0, 10, 20). Readers following the spec will mis-handle subprocess failures and Django ingest mapping.

## Scope

- Amend `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md` §6 exit-code table to match `ExitCode` in `src/shapez2_factory/interfaces/cli/asteroid_solve.py`.
- Grep and update cross-references in docs that cite legacy integers 1–5.
- Add mapping note in Django subprocess runner docs/code comments if ingest maps exit codes.

## Non-goals

- Do not change runtime exit codes without explicit contract change and regression tests.
- Do not collapse `VALIDATION_FAILED` with legacy `RTTP_VALIDATION_FAILED` semantics.

## Implementation Plan

1. Read `ExitCode` enum and all `main()` return paths in `src/shapez2_factory/interfaces/cli/asteroid_solve.py`; record authoritative mapping (0=OK, 10=VALIDATION_FAILED, 20=STACK_UNAVAILABLE).
2. Open artifact design spec §6; replace stale table (0–5) with implemented codes; note argparse reserves low integers for future expansion.
3. Run `rg 'exit.?code|ExitCode|exit [0-5]' docs/` and update or mark superseded any stale references.
4. Check `django_apps/` subprocess runner (`solver_subprocess_runner` or equivalent) for exit-code handling; add short comment or doc link to canonical table if mapping exists.
5. Verify `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/checklist.md` remains consistent with amended spec.
6. Confirm `tests/unit/shapez2_factory/test_cli_exit_codes.py` still documents intended behavior; extend only if a doc-linked assertion is missing.

## Files / Areas Likely Affected

- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md`
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (read-only unless mapping comment added)
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/checklist.md`
- `tests/unit/shapez2_factory/test_cli_exit_codes.py`
- Django subprocess runner module (TBD — grep `STACK_UNAVAILABLE` / `ExitCode` under `django_apps/`)

## Validation Plan

- lint: `ruff check .` (no production code change expected)
- typecheck: `mypy django_apps config src` (if runner comments only, skip or spot-check)
- tests: `powershell -File scripts/test_fast.ps1` or targeted `pytest tests/unit/shapez2_factory/test_cli_exit_codes.py`
- build: N/A (docs-only)
- manual verification: Grep docs for legacy exit integers 2–5; confirm spec §6 matches `ExitCode` enum

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Whether to add ADR vs inline spec amendment — issue allows either; prefer minimal spec edit unless team wants ADR.
- Related issues SHA-8/9/10/11 may reference exit semantics; cross-link only, do not expand scope.
