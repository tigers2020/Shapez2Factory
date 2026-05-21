# Risks and Open Questions — `prefabs.json`

## Uncertain meaning

| Item | Risk |
| ---- | ---- |
| No prefab internals | Cannot simulate from DB |
| 764 vs 131 building variants | Many visual rows per logical building |
| `path_family` parser | False grouping on ambiguous names |

## Human review

| Question |
| -------- |
| Store LOD rows separately or collapse to parent prefab? |
| Planner needs prefab_asset or only meta bridge? |

## Runtime traps

- Model named `UnityEngineObject` — reject
- Using `prefab_path` as PK without normalizing case — paths are case-sensitive

## Ambiguous IDs

- `stable_id` reliable (764 unique)
- `display_name_key` equals path until translations exist

## Version drift

- `manifest.file_hashes.prefabs.json` — large file, CI must hash full bytes

## Missing targets

| Target | Status |
| ------ | ------ |
| `building_variants` FK | Not in JSON |
| Unity mesh GUIDs | Not exported |
| `translations.json` | Empty |

## Deferred tables

| Table | Reason |
| ----- | ------ |
| `prefab_component` | No data |
| `prefab_lod_group` | Would need parent-child rules |

## Highest risk

**Import order:** `asset_references` before prefabs breaks 764 FK checks. Mitigation: documented pipeline + integration test.
