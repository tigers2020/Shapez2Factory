# Risks and Open Questions — `sprites.json`

## Uncertain meaning

| Item | Risk |
| ---- | ---- |
| No atlas/UV data | Icons not renderable from DB alone |
| `icon_family` parser | Heuristic only |

## Human review

| Question |
| -------- |
| Link icons to buildings by name convention? |
| Drop redundant `logical_path` column? |

## Runtime traps

- Model `UnityEngineObject`

## Ambiguous IDs

- `stable_id` reliable here (61 unique)

## Version drift

- Manifest hash on change

## Missing targets

| Target | Status |
| ------ | ------ |
| translations | empty |
| Texture assets | not exported |

## Deferred

| Table | Reason |
| ----- | ------ |
| `sprite_atlas_region` | No data |

## Highest risk

**asset_references before sprites** — 61 broken FKs. **Mitigation:** documented import order + test.
