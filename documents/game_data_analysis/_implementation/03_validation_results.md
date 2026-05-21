# Validation Results

## Commands

```bash
python manage.py makemigrations game_data
python manage.py migrate game_data
python -m pytest tests/unit/game_data -q
python -m ruff check django_apps/game_data tests/unit/game_data --fix
```

## pytest

```text
49 passed in ~152s
```

Files:

- `tests/unit/game_data/test_no_raw_json_domain_storage.py`
- `tests/unit/game_data/test_models.py`
- `tests/unit/game_data/test_import_idempotency.py`
- `tests/unit/game_data/test_cross_references.py`

## Coverage highlights

- No forbidden `JSONField` on domain models (`SimulationRuntimeAudit` only).
- Full bundle import idempotent on `documents/game_data`.
- Toolbar placements resolve `BuildingVariant` via `Definitions[0].Id.Name`.
- Asset meta links content assets.
- Runtime CLR strings rejected as toolbar/shape canonical IDs; CLR registry uses hashed canonical_id.
