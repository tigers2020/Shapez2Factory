# django_apps/shapez_solver AGENTS.md

## Scope

Recipe graph solver projects/runs, macro patterns, graph DTOs, operation engine adapters, and pattern lab services.

## Rules

- This domain is separate from Asteroid Lab runtime decisions.
- Keep graph validation and operation semantics in domain/services, not views/templates.
- Preserve recipe graph topology and carrier contracts unless canon changes.
- Persisted model changes need migrations and focused model/service tests.
- Do not couple recipe graph logic to Asteroid Lab layer stack internals.

## Verify

- `python -m pytest tests/unit/shapez_solver/`
- Include graph fixture tests when topology, carriers, or clipboard formats change.
