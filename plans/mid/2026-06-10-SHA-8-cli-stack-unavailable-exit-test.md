---
linear_issue: SHA-8
title: Missing regression coverage for asteroid_solve ExitCode.STACK_UNAVAILABLE (20)
priority: Mid
labels:
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Missing regression coverage for asteroid_solve ExitCode.STACK_UNAVAILABLE (20)

## Source Issue

- Linear: SHA-8
- Status at planning time: Todo
- Priority: Mid

## Problem

`asteroid_solve run` returns `ExitCode.STACK_UNAVAILABLE` (20) when the stack writes an artifact but `RunStackUseCase` reports `ok=False`. No unit test asserts this exit mapping, leaving BA-7 subprocess contract partially unverified.

## Scope

Add CLI unit test forcing `result.ok=False` and asserting exit 20 with artifact directory present.

## Non-goals

- Do not change exit code values.
- Do not add broad golden-loop coverage.

## Implementation Plan

1. Open `tests/unit/shapez2_factory/test_cli_exit_codes.py` and review existing OK/VALIDATION_FAILED patterns.
2. Add `test_run_returns_stack_unavailable_when_stack_fails`: monkeypatch `RunStackUseCase.run` to return `StackRunResult(ok=False, ...)`.
3. Invoke `main(["run", ...])` with minimal valid args/fixture used by sibling tests.
4. Assert return code `ExitCode.STACK_UNAVAILABLE` (20) and stderr/log contains `ok=false` per issue spec.
5. Run `pytest tests/unit/shapez2_factory/test_cli_exit_codes.py -v`.

## Files / Areas Likely Affected

- `tests/unit/shapez2_factory/test_cli_exit_codes.py`
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (read-only)
- `src/shapez2_factory/application/asteroid_lab/run_stack.py` (patch target)

## Validation Plan

- lint: `ruff check tests/unit/shapez2_factory/test_cli_exit_codes.py`
- typecheck: N/A (test-only)
- tests: `pytest tests/unit/shapez2_factory/test_cli_exit_codes.py -v`
- build: N/A
- manual verification: Confirm no `STACK_UNAVAILABLE` references missing in tests after add

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Cross-link SHA-7 exit-code doc alignment after SHA-7 lands (Low item in SHA-8).
