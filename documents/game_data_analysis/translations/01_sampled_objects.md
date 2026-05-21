# Random Sampling — `translations.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | Indices `0 .. N-1` where **N = 0** |
| Sample size rule | Fewer than 3 groups → sample **all available** |
| **Sampled array elements** | **none** (empty population) |

```python
import random
N = 0
random.Random(20260521).sample(range(N), min(3, N))  # ValueError / []; cannot draw 3
```

**Procedure used:** No in-file random elements exist. Supplemental **structural evidence** below is drawn from `manifest.json` and cross-file `LazyLocalizedText` patterns (not counted as random samples of `translations.json` rows).

---

## Evidence A — manifest incomplete flag (export metadata)

```json
{
  "incomplete_sections": ["translations"],
  "warnings": [
    "translations: ILocalizationDatabaseProvider not found in scene."
  ],
  "file_hashes": {
    "translations.json": "sha256:4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
  }
}
```

**Interest:** Explains empty `[]` — localization provider missing at dump time.

---

## Evidence B — inferred future row shape (from `building_groups.json`, not a translation row)

```json
{
  "Title": {
    "Id": { "Id": "building-variant.BeltDefaultVariant.title" },
    "PlaceholderResolver": { "Replacements": {} },
    "$type": "Core.Localization.LazyLocalizedText"
  }
}
```

**Interest:** Defines expected **`message_key`** format when `translations.json` is populated in a future export.

---

## Evidence C — empty file literal

```json
[]
```

**Interest:** Integrity hash is SHA-256 of empty array; importers must not treat as error silently.

---

## Full-file patterns

| Pattern | Evidence |
| ------- | -------- |
| Zero rows | `len == 0` |
| Hash matches `[]` | manifest + computed |
| Keys live elsewhere | LazyLocalizedText only in sibling files |

## Traceability

When rows exist → `localized_message(message_key, locale, text, …)`; today → `localization_export_status` only.
