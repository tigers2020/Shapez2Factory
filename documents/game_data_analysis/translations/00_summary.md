# File Inventory — `translations.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/translations.json` |
| File name | `translations.json` |
| File size | **2 bytes** (literal `[]`) |
| Manifest hash | `sha256:4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| SHA-256 of `[]` | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` (matches manifest) |
| Dump context | `manifest.json` → `incomplete_sections: ["translations"]` |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **0** |
| Top-level keys | N/A (no objects) |

## Major object groups

| Group | Count |
| ----- | ----- |
| Translation records | **0** |
| Nested structures | **none** |

## Repeated structures

Not observable in this export. **Inferred** from sibling dumps (`building_groups.json`, `toolbar_entries.json`) where UI strings use:

```text
Core.Localization.LazyLocalizedText
  └─ Id.Id  e.g. building-variant.BeltDefaultVariant.description
  └─ PlaceholderResolver.Replacements
```

## Arrays detected

- Empty root array only.

## Candidate IDs (future / cross-file)

| Field (expected when populated) | Role |
| --------------------------------- | ---- |
| `message_key` / `Id.Id` | Canonical string key for lookup |
| `locale` / `language` | Locale dimension (not present in empty file) |
| `stable_id` | Would be per-row dump hash if exporter adds rows |

## Runtime / reflection / debug

| Item | Notes |
| ---- | ----- |
| `ILocalizationDatabaseProvider not found in scene` | manifest warning — export failed |
| `LazyLocalizedText`, `LazyLocalizedTextPlaceholderResolver` | Appear in **other** JSON files, not in `translations.json` |

## Source metadata

- Empty file is **valid artifact** proving capture failure, not absence of game strings.
- `manifest.file_hashes.translations.json` still listed for integrity gate.

## Cross-file references (unresolved strings)

| File | Pending need |
| ---- | ------------ |
| `building_groups.json` | `LazyLocalizedText` titles/descriptions |
| `toolbar_entries.json` | `Title` / `Description` cycles |
| `research_unlocks.json` | Human-readable titles |
| `materials.json`, `sprites.json` | `display_name_key` currently equals path |

## Design implication

Do **not** create empty `translations_raw_json` or skip import — record **`localization_export_status`** (incomplete) and define **`localized_message`** schema for **future** non-empty dumps. Import pipeline must pass with **zero rows** and explicit audit flag.
