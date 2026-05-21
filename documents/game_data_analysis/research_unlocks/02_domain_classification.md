# Domain Classification — `research_unlocks.json`

## Row envelope

| JSON path | Classification |
| --------- | -------------- |
| `[i].stable_id` | source metadata (non-unique) |
| `[i].source_type_name` | enum / choice (row discriminator) |
| `[i].source_guid`, `source_path` | source metadata |
| `[i].display_name_key` | entity attribute / i18n |
| `[i].simulation_parameters` | source metadata |
| `[i].definition_snapshot` | source metadata wrapper |
| `[i].manager_snapshot` | runtime / reflection / debug metadata |
| `[i].progression_layout` | ordered child record (decompose) |
| `[i].research_config` | entity attribute group → config table |

## Snapshot fields (quest / level / side upgrade)

| Path | Classification |
| ---- | -------------- |
| `Id`, `Id.Id` | entity attribute (canonical key) |
| `Title`, `Description`, `IconId`, `VideoId`, `ImageId` | entity attribute |
| `Costs[]` | ordered child record |
| `Costs[].ShapeHash` | relationship → `shape_recipe` |
| `Costs[].Amount` | entity attribute |
| `Rewards[]` | ordered child record |
| `Rewards[].$type` | enum / choice |
| `RequiredUpgrades[]` | relationship (M2M) |
| `RequiredMechanics[]` | relationship (M2M) |
| `Lines[]` | ordered child record (level only) |
| `<*k__BackingField>` | runtime metadata — **skip import** |
| `$type` | source metadata |

## Rejected as domain tables

| Name | Reason |
| ---- | ------ |
| `ResearchUnlockManager` | Singleton dump type |
| `Game.Core.Research.ResearchUpgradeId` | CLR type label |
| `ResearchCostShapes` | `$type` label, not table |

## Inferred domain entities

| Entity | Rows |
| ------ | ---- |
| Research upgrade | 168+ keys |
| Research milestone (level) | 13 |
| Research side quest | 188 |
| Research side upgrade | 51 |
| Research mechanic | 4 |
| Global config | 1 |
| Progression graph edges | from manager layout |
