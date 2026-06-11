# File Inventory — `research_unlocks.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/research_unlocks.json` |
| File name | `research_unlocks.json` |
| File size | **~1,700,238 bytes** |
| Manifest hash | `sha256:f9f7f226c937bd9e6810aa01c7ccfcd3db1409e3928531814c7657c3118941a3` |
| Dump context | `manifest.json` → `runtime_reflection`, v2 export |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **436** |
| Row kinds | **8** `source_type_name` values (mixed envelopes) |

## Envelope patterns

| Pattern | Rows | Top-level keys |
| ------- | ---- | -------------- |
| Standard snapshot | ~434 | `stable_id`, `source_*`, `definition_snapshot`, often `simulation_parameters` |
| Manager root | **1** | `manager_snapshot`, `progression_layout`, `research_config` at **top level** (no `definition_snapshot`) |

## `source_type_name` distribution

| `source_type_name` | Count | Role |
| ------------------ | ----- | ---- |
| `ResearchSideQuest` | 188 | Side quest definitions |
| `Game.Core.Research.ResearchUpgradeId` | 168 | Upgrade id registry entries |
| `ResearchSideUpgrade` | 51 | Side upgrade nodes |
| `ResearchLevel` | 13 | Milestone / level nodes |
| `Game.Core.Research.ResearchMechanicId` | 4 | Mechanic gates |
| `ResearchUnlockManager` | 1 | Full progression graph + config |
| `ResearchConfig` | 1 | Global research config |
| `ResearchProgression` | 1 | Progression wrapper |

## `definition_snapshot` internals (varies by row kind)

| Inner structure | Present on | Notes |
| --------------- | ---------- | ----- |
| `Id` | Quest / upgrade / level | Often **`{"Id": "SG_…"}`** dict, not plain string |
| `Title`, `Description`, `IconId`, … | Quest, level, side upgrade | UI / wiki metadata |
| `Costs[]` | Quest, level | `ResearchCostShapes` with **`ShapeHash`** |
| `Rewards[]` | Quest, level | Typed rewards (`$type`) |
| `RequiredUpgrades`, `RequiredMechanics` | Quest, level | Prerequisite lists |
| `Lines[]` | `ResearchLevel` only | Per-line costs / reuse flags |
| `Id` string only | `ResearchUpgradeId` rows | e.g. `SG_Trains_4_2` |

## `progression_layout` (manager row only)

| Child key | Observed size |
| --------- | ------------- |
| `Levels` | 13 |
| `SideUpgrades` | 51 |
| `SideQuests` / groups | large |
| `AllUpgrades` | 129 |
| `LinearUpgrades` | dict (7 hubs) |
| `ShopItems`, `WikiConfiguration`, … | audit / review |

## Major object groups

| Group | Count | Domain role |
| ----- | ----- | ------------- |
| Upgrade identifiers | 168+ | Unlock tree keys |
| Side quests | 188 | Optional research branches |
| Milestone levels | 13 | Main progression ladder |
| Side upgrades | 51 | Per-category upgrades |
| Mechanics | 4 | Gating flags |
| Global graph | 1 manager | Authoritative layout index |

## Repeated structures

- `ResearchCostShapes`: `Amount`, `ShapeHash` (links to `items.json` `Hash`)
- Backing-field duplicates: `<Field>k__BackingField` mirrors public fields — **import public names only**
- `$type` on nested DTOs — source metadata

## Arrays / nested objects

- Deep nesting under `progression_layout`, `Lines`, `Costs`, `Rewards`
- **Do not** store these trees as domain JSONField blobs

## Candidate IDs

| Field | Canonical? |
| ----- | ---------- |
| `definition_snapshot.Id.Id` (normalized) | **Yes** — upgrade / quest / milestone key |
| `ResearchUpgradeId` row `Id` string | **Yes** for upgrade registry |
| `stable_id` | **No** — 268 unique / 436 rows; **168 duplicate** (level + upgrade id pairs) |
| `ShapeHash` in costs | **Yes** — FK to `shape_recipe.shape_hash` |
| `source_type_name` | Dump discriminator only |

## Runtime / reflection / debug

- `Game.Core.Research.ResearchUpgradeId`, `ResearchUnlockManager`, `$type` strings
- `<*k__BackingField>` property names
- `manager_snapshot` delegate/handler names — audit only

## Cross-file references

| File | Relationship |
| ---- | ------------ |
| `items.json` | `ShapeHash` in research costs |
| `building_groups.json` / `toolbar_entries.json` | Inferred unlock targets by upgrade id string |
| `translations.json` | Empty — titles not resolved |
| `raw_type_index.json` | CLR types for research classes |

## Design implication

Decompose into **`research_upgrade`**, **`research_milestone`**, **`research_side_quest`**, **`research_side_upgrade`**, **`research_mechanic`**, child **`research_cost` / `research_reward` / `research_prerequisite`**, and **`research_global_config`** — import manager `progression_layout` into normalized graph tables, not `research_unlocks_raw_json`.
