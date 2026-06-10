# django_apps/shapez_core AGENTS.md

## Scope

Shape primitives, parsing, normalization, operations, crystal geometry, render scenes, and preview API helpers.

## Rules

- Keep shape parsing and operation semantics deterministic.
- Treat fixture and IVVD alignment tests as contract tests, not snapshot noise.
- Services may compose responses; domain modules own shape rules.
- Do not add web-only display shortcuts to parser or operation semantics.
- Preserve API response compatibility unless a current contract updates it.

## Verify

- `python -m pytest tests/unit/shapez_core/`
- Add operation or parser regression tests for semantic changes.
