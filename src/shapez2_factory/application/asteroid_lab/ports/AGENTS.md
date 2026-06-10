# src/shapez2_factory/application/asteroid_lab/ports AGENTS.md

## Scope

Application boundary interfaces between pure Asteroid Lab core and external adapters.

## Rules

- Ports describe required capabilities; adapters implement them outside the pure core.
- Keep port DTOs serializable, explicit, and Django-free.
- Do not leak ORM objects, QuerySets, HTTP requests, or settings into port contracts.
- Contract changes need caller and adapter updates in the same PR-sized change.

## Verify

- Focused port/import tests plus `tests/unit/architecture/` boundary tests.
