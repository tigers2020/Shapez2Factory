# Reconstructed Schema — `translations.json`

**Current export:** zero rows. Schema defines **target** tables for when data exists plus **status** row today.

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `localization_export_status` | Export outcome | Was localization captured? | manifest + empty file | import batch | Observed |
| `localized_message` | String catalog | What is the display text for key K in locale L? | future `[*]` | all UI dumps | Planned (empty) |
| `localized_message_placeholder` | Template slots | Placeholder replacements? | future | message | Planned |
| `game_data_import_batch` | Provenance | Which dump? | manifest | → all | Observed |
| `unknown_property` | Extensions | New keys | any | audit | Planned |

---

## `localization_export_status`

| Column | Meaning | Source | Inferred? |
| ------ | ------- | ------ | --------- |
| `import_batch_id` | FK | manifest | yes |
| `is_empty` | `true` for this dump | file length 2 | observed |
| `is_incomplete` | manifest flag | `incomplete_sections` | observed |
| `failure_reason` | Export warning text | manifest.warnings | observed |
| `expected_hash` | `sha256:4f53cda…` | manifest | observed |

**Domain question:** “Should importers require translation rows for this bundle?” → **No** for this export.

---

## `localized_message` (planned — 0 rows today)

| Column | Meaning | Source (future) | Constraints |
| ------ | ------- | --------------- | ----------- |
| `id` | PK | surrogate | PK |
| `message_key` | Stable key | `Id.Id` in LazyLocalizedText | UNIQUE per locale |
| `locale_code` | e.g. `en` | TBD in future dump | |
| `message_text` | Resolved string | export body | |
| `import_batch_id` | FK | manifest | FK |

**Unique:** `(message_key, locale_code)`.

**Human review:** Exact future JSON row shape unknown until successful dump.

---

## Anti-patterns rejected

| Rejected | Why |
| -------- | --- |
| `translations_raw_json` storing `[]` | No value |
| Skipping import | Breaks manifest integrity checks |
| Using `display_name_key` as final UI text | Keys only in other files |
