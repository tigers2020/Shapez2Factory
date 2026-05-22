# game_data Tier A — manual CI / release gate

**Owner:** django `game_data`  
**Not part of:** `test_fast`, default PR `test-fast` matrix, or unit pytest.

Tier **B** (`game_data_backup/game_data_dump.json`) is the only full-bundle seed for unit pytest. This runbook is **required before** committing an updated Tier B dump.

## When to run

- Normalized models or import semantics changed
- `documents/game_data/` interchange bundle refreshed from game export
- `PINNED_MANIFEST_HASH` or `_dump_expectations.py` must change

## Prerequisites

- `documents/game_data/` present with valid `manifest.json` (Tier A source; may live outside repo in CI)
- Local SQLite: `$env:DJANGO_USE_SQLITE = "1"` (PowerShell) or `export DJANGO_USE_SQLITE=1`

## Gate sequence

From repository root:

```powershell
$env:DJANGO_USE_SQLITE = "1"
python manage.py migrate game_data
python manage.py flush --no-input
python manage.py import_game_data --source documents/game_data
python manage.py seed_game_data_taxonomy
python manage.py dumpdata game_data --indent 2 -o game_data_backup/game_data_dump.json
python manage.py import_game_data --verify
```

Then update pytest pins in the same PR:

1. Set `PINNED_MANIFEST_HASH` in `tests/unit/game_data/_dump_expectations.py` from the new `ImportBatch.manifest_self_hash`
2. Recompute ORM counts (script or SQLite query) and update `_dump_expectations.py`
3. Verify unit slice:

```powershell
python -m pytest tests/unit/game_data/ --durations=20
powershell -File scripts/test_fast.ps1
```

## pytest Tier B contract

- Fixture: `tests/unit/game_data/fixtures.py` → `loaddata` + pinned batch assert
- Missing dump: **fail** when `CI` or `REQUIRE_GAME_DATA_DUMP=1`; local may skip
- Do **not** call global `flush` in pytest; use app-local `_flush_committed_game_data` only

## Related

| Doc | Role |
|-----|------|
| [game_data_coverage.md](../domain/game_data_coverage.md) | A vs B boundary |
| [game_data_snapshot_deploy.md](game_data_snapshot_deploy.md) | Asteroid snapshot deploy (consumer) |
| [Spec: pytest dump-only](../superpowers/specs/2026-05-22-game-data-pytest-dump-only-design.md) | Design |
