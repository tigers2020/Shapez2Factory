# Domain Classification — `sprites.json`

| JSON path | Classification | Notes |
| --------- | -------------- | ----- |
| `[i]` | domain entity | → `sprite_asset` |
| `[i].stable_id` | entity attribute | UNIQUE |
| `[i].sprite_path` | entity attribute | UNIQUE |
| `[i].source_path` | entity attribute | redundant with sprite_path |
| `[i].display_name_key` | entity attribute | i18n key (= path today) |
| `[i].source_type_name` | source metadata | `UnityEngine.Object` |
| `[i].source_guid` | source metadata | empty |
| Icon family prefix | unknown / inferred | `LogicGate`, `Belt`, etc. |

## Rejected

| Label | Reason |
| ----- | ------ |
| `UnityEngineObject` | runtime label |
| Table per icon path | 61 mirror tables |

## Entity

**Sprite asset** (icon content registry) — 61 instances.
