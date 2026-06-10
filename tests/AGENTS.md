# tests AGENTS.md

## Scope

Unit, integration, architecture, fixture, golden, and support tests.

## Rules

- Tests verify current contracts, not agent guesses.
- Regression tests should fail before the fix unless impossible.
- Do not skip, xfail, delete, weaken, or relax tests to force green.
- Golden fixtures are contract artifacts; update only with explicit reason and reviewer-visible diff.
- Shared helpers belong in `tests/support/`; keep test-local helpers local when reuse is not real.
- Name tests by behavior or regression, not implementation trivia.

## Verify

- Run the smallest meaningful test path first, then broaden only for shared contracts.
- Architecture tests are mandatory when import boundaries or module ownership changes.
