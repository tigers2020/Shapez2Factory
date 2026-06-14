# Game data import boundary — contract

**Thread:** `game-data-import-boundary`  
**Approved:** 2026-06-14

## Scope

Introduce `django_apps/game_data/services/bundle_gate` for path resolution and fail-closed manifest/file hash validation before any ORM import. Wire CLI `import_game_data`, `verify_game_data_source`, and test path helpers (`dump_paths.py` delegates to production resolver).

## Non-goals

- Split `GameDataImporter` by artifact
- Unify snapshot export modules
- Wire `assert_canonical_ids_unique`
- JSON schema validation of artifact contents

## Decisions

| ID | Decision |
|----|----------|
| D1 | Production owns path candidates: `documents/game_data`, then `documents/knowledge/raw/game_data` |
| D2 | Fail-closed on hash mismatch; no `--force` |
| D3 | Missing files allowed only when listed in `manifest.incomplete_sections` |
| D4 | `--verify` = `validate_game_data_bundle()` + DB batch reconcile |
| D5 | Migration precheck stays in `import_guards` (not gate) |
| D6 | `GameDataImporter` accepts `GameDataBundle` only |

## Invariants

- Gate never touches the database
- Post-gate import records `ArtifactChecksum.import_status="ok"` for gate-validated files
- `manifest_self_hash` computed from raw `manifest.json` bytes via `sha256_file`

## Boundaries

| Module | Owns |
|--------|------|
| `bundle_gate.py` | Path resolve, disk integrity |
| `import_guards.py` | Migrations, post-import JSONField ban |
| `import_verify.py` | Gate + DB reconcile |
| `GameDataImporter` | ORM mapping after validated bundle |

## Forbidden

- Record-and-continue on checksum mismatch during import
- Duplicate path candidate tuples in tests (must delegate to production)

## Validation

```bash
python -m pytest tests/unit/game_data/test_bundle_gate.py tests/unit/game_data/test_dump_paths.py tests/unit/game_data/test_import_guards.py -q
python -m pytest tests/unit/game_data/test_space_transport_layout_import.py -q
ruff check django_apps/game_data/
```
