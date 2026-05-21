# Cross-Reference Analysis — `translations.json`

## Current state

```text
game_data_import_batch
  └─ has one → localization_export_status (is_empty, is_incomplete)

localized_message
  └─ (no rows — all display keys in other files unresolved)
```

## Intended (future)

```text
localized_message
  ├─ resolves → building_groups titles/descriptions (by message_key)
  ├─ resolves → toolbar_entries labels
  ├─ resolves → research_unlock titles
  └─ optional → materials/sprites display_name_key
```

## FK relationships today

| From | To | Status |
| ---- | -- | ------ |
| Other dumps → `localized_message` | N/A | **blocked** — empty catalog |

## M2M / ordered children

None in current file. Future placeholders may be child rows of `localized_message`.

## Inferred references

| Reference | Status |
| --------- | ------ |
| manifest incomplete flag | **resolved** |
| SHA-256 of `[]` | **resolved** |
| `building-variant.*.title` keys | **unresolved** |

## Source metadata

- Export failure provider name in warning only
