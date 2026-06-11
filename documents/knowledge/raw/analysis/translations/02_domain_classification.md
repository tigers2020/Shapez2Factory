# Domain Classification — `translations.json`

## Current file (`[]`)

| Path | Classification |
| ---- | -------------- |
| `[root]` | empty array — no domain rows |

## Expected fields (future export — inferred)

| Path | Classification |
| ---- | -------------- |
| `[i].message_key` / `Id` | entity attribute (canonical) |
| `[i].locale` | entity attribute / enum |
| `[i].text` / `value` | entity attribute |
| `[i].placeholders` | ordered child record |
| `[i].stable_id` | source metadata |
| `$type: LazyLocalizedText` | source metadata |
| `ILocalizationDatabaseProvider` | runtime / reflection / debug metadata |

## Cross-file (today)

| Location | Classification |
| -------- | -------------- |
| `building_groups` Title/Description | unknown — needs `localized_message` FK by key |
| `display_name_key` when == path | source metadata until translation join works |

## Rejected

| Label | Reason |
| ----- | ------ |
| Table `LazyLocalizedText` | CLR type name |
| Table `ILocalizationDatabaseProvider` | Provider type |
| `raw_json []` as domain row | Empty dump |
