# Validation Plan — `translations.json`

> **pytest:** [documents/ai/manuals/testing.md](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **forbidden**.

`tests/unit/game_data_import/test_translations_import.py`

| # | Invariant |
| - | --------- |
| 1 | Import succeeds with 0 `localized_message` rows |
| 2 | `localization_export_status.is_empty is True` |
| 3 | `localization_export_status.is_incomplete is True` |
| 4 | File hash equals SHA-256 of `[]` |
| 5 | Manifest `incomplete_sections` includes `translations` |
| 6 | Idempotent re-import |
| 7 | No `translations_raw_json` table |
| 8 | No domain PK named `LazyLocalizedText` |
| 9 | Other importers pass without translation FK when batch flagged incomplete |
| 10 | Future fixture: non-empty sample populates `localized_message` |

## Golden

`tests/golden/game_data/translations/empty_bundle.json` — hash + status flags.
