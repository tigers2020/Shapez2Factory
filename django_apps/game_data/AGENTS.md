# django_apps/game_data AGENTS.md

## Scope

Canonical game dump ORM, importers, validators, identifiers, staff browse, and game-data snapshots.

## Rules

- Concrete normalized fields and relations are preferred over domain JSON blobs.
- Importers must be deterministic and preserve provenance needed by tests.
- Browse/admin views stay thin; domain classification belongs in services/importers.
- Snapshot selectors must remain stable enough for solver and Asteroid Lab fixtures.
- Cross-reference and identifier logic must not silently create unknown categories.

## Verify

- `python -m pytest tests/unit/game_data/`
- Add focused regression fixtures when importer behavior or taxonomy changes.
