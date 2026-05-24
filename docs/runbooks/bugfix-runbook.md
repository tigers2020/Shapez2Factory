# Bug Fix Runbook

This runbook is the standard procedure for bug fix work. Use it together with the `bug-fix` skill (`.cursor/skills/bug-fix/SKILL.md`).

## Prerequisites

- You must have input or logs that can reproduce the bug.
- If reproduction is not possible, stop with `BLOCKED: missing context` and request additional information.

## Procedure

### 1. Confirm reproduction

```bash
# Reproduction test or direct execution
pytest tests/ -k "<related test name>" -v
```

If no reproduction test exists, write one first (see `write-tests` skill).

### 2. Root cause analysis

1. Find the initial error location from the stack trace / logs.
2. Identify the relevant layer (domain / application / adapters / interfaces).
3. If a layer boundary is violated, compare against `docs/architecture/README.md`.
4. Narrow down to 1–2 hypotheses.

### 3. Fix

- Smallest diff principle: remove the root cause with minimal change.
- If domain rules change, confirm with Dominic; if application, with Yuri; if adapter, with Ada.
- If the design decision changes, add an ADR in `docs/adr/`.

### 4. Verification

```bash
python -m pytest            # Full suite (-q / --quiet / --tb=no forbidden)
ruff check .                # Lint
mypy django_apps config src # Type check
black --check .             # Format
```

Declare completion only after all steps pass.

### 5. Completion report

```
Summary: (one-line bug cause)
Files changed:
Commands run: python -m pytest / ruff check . / mypy django_apps config src / black --check .
Validation: (pass/fail details)
Risks / follow-up:
Docs updated:
```

## Common mistakes

| Mistake | Correct action |
|---|---|
| Fixing without a test | Write a reproduction test first |
| Adding I/O to domain | Separate into adapter/port |
| Declaring completion before verification | Declare only after step 4 verification |
| Not adding a regression test | Add at least one test to prevent the same class of regression |

## References

- [bug-fix skill](../../.cursor/skills/bug-fix/SKILL.md)
- [Architecture](../architecture/README.md)
- [AGENTS.md](../../AGENTS.md)
