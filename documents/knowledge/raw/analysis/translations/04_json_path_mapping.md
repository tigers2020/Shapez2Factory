# JSON Path Mapping — `translations.json`

## Current file (empty)

| JSON path | Observed meaning | Classification | Target table | Target column | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ----- |
| `[root]` | Empty array | source metadata | `localization_export_status` | `is_empty=true` | |
| (no `[i].*` paths) | — | — | — | — | |

## Manifest paths

| JSON path | Target | Column |
| --------- | ------ | ------ |
| `manifest.incomplete_sections[translations]` | `localization_export_status` | `is_incomplete` |
| `manifest.warnings[translations:*]` | `localization_export_status` | `failure_reason` |
| `manifest.file_hashes.translations.json` | artifact checksum | `expected_hash` |

## Future (inferred)

| JSON path | Target table | Target column |
| --------- | ------------ | ------------- |
| `[i].key` / `Id.Id` | `localized_message` | `message_key` |
| `[i].locale` | `localized_message` | `locale_code` |
| `[i].text` | `localized_message` | `message_text` |

## Cross-file keys (unresolved today)

| Source path | Needs |
| ----------- | ----- |
| `building_groups.*.Title.Id.Id` | `localized_message.message_key` |
| `toolbar_entries.*.Title` LazyText | same |
