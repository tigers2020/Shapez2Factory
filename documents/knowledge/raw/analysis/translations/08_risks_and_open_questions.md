# Risks and Open Questions — `translations.json`

## Uncertain meaning

| Item | Risk |
| ---- | ---- |
| Future row JSON shape | Exporter not observed yet |
| Locale dimension | Unknown until successful dump |
| Whether keys duplicate `display_name_key` | May differ |

## Human review

| Question |
| -------- |
| Block UI import on incomplete translations? |
| Fallback: show `message_key` vs English path? |
| Re-export procedure when provider available? |

## Runtime traps

- Treating empty `[]` as import error
- Model `ILocalizationDatabaseProvider`

## Ambiguous IDs

- Today: no IDs in file
- Cross-file: use `message_key` from LazyText `Id.Id`, not `stable_id` from other dumps

## Version drift

- Hash `4f53cda…` stable while empty
- Any non-empty export changes hash — CI must update golden

## Missing targets

| Target | Status |
| ------ | ------ |
| All LazyLocalizedText resolutions | **missing** |

## Deferred

| Table | Reason |
| ----- | ------ |
| `localized_message` data | No rows |
| `locale` reference table | Unknown codes |

## Highest risk

**Other importers assume translation rows exist** and fail FK validation. **Mitigation:** `localization_export_status.is_incomplete` gate + tests allowing zero messages for this bundle.
