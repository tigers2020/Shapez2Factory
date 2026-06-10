# src/shapez2_factory AGENTS.md

## Scope

Django-free solver core, CLI interfaces, DTOs, artifact writers, and pure application services.

## Rules

- No imports from `django_apps`, Django settings, ORM models, or request objects.
- CLI/core paths must accept explicit inputs and emit deterministic artifacts.
- Artifact writes must stay atomic and hash/version aware.
- Keep DTOs importable without Django.
- Use enums/constants for failure, event, and issue codes; avoid stringly-typed drift.
- Do not read `var/` debug output as canon.

## Verify

- `python -m pytest tests/unit/shapez2_factory/ tests/unit/architecture/`
- Run focused CLI/artifact tests for interface or artifact changes.
