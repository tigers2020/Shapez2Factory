# Reconstructed Schema — `research_unlocks.json`

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `research_upgrade` | Upgrade registry | What unlock keys exist? | `ResearchUpgradeId`, embedded ids | quests, buildings (inferred) | Observed |
| `research_milestone` | Main ladder | What milestone levels exist? | `ResearchLevel` | costs, rewards, prereqs | Observed |
| `research_side_quest` | Side content | What side quests exist? | `ResearchSideQuest` | costs, rewards, prereqs | Observed |
| `research_side_upgrade` | Branch upgrades | What side upgrades exist? | `ResearchSideUpgrade` | prereqs | Observed |
| `research_mechanic` | Mechanic gates | What mechanics must be unlocked? | `ResearchMechanicId` | prereqs | Observed |
| `research_unlock_cost` | Shape costs | What shape payment unlocks node N? | `Costs[]`, `Lines[].Costs[]` | `shape_recipe` | Observed |
| `research_unlock_reward` | Rewards | What does completing node grant? | `Rewards[]` | — | Observed |
| `research_prerequisite` | Dependencies | Which upgrades/mechanics required? | `RequiredUpgrades`, `RequiredMechanics` | upgrade, mechanic | Observed |
| `research_global_config` | Tunables | Global research rules? | `research_config` | — | Observed |
| `progression_layout_*` | Graph index | How does manager index nodes? | `progression_layout` | all above | Inferred |
| `game_data_import_batch` | Provenance | Which dump? | manifest | → all | Observed |
| `unknown_property` | Extensions | New keys? | any | audit | Planned |

---

## `research_upgrade`

| Column | Source | Constraints |
| ------ | ------ | ------------- |
| `upgrade_key` | `definition_snapshot.Id` (string) or `Id.Id` | **UNIQUE** |
| `dump_stable_id` | envelope `stable_id` | not unique |
| `import_batch_id` | manifest | FK |

**Domain question:** “What is the canonical unlock identifier (e.g. `SG_Trains_4_2`)?”

---

## `research_milestone` / `research_side_quest` / `research_side_upgrade`

Shared columns (per entity table):

| Column | Meaning |
| ------ | ------- |
| `node_key` | Normalized `Id.Id` |
| `title`, `description`, `icon_id`, … | snapshot scalars |
| `import_batch_id` | FK |

**Unique:** `node_key` per table.

---

## `research_unlock_cost`

| Column | Meaning |
| ------ | ------- |
| `parent_kind` | milestone / side_quest / line |
| `parent_id` | FK |
| `sort_order` | array index |
| `shape_hash` | `ShapeHash` |
| `amount` | int |

**FK:** `shape_hash` → `shape_recipe.shape_hash` (validate against `items.json`).

---

## `research_prerequisite`

| Column | Meaning |
| ------ | ------- |
| `parent_kind`, `parent_id` | owning node |
| `required_upgrade_key` | FK `research_upgrade` |
| `required_mechanic_key` | FK `research_mechanic` |

---

## `research_global_config`

Scalars from `research_config` (not nested layout): `InitialResearchPoints`, `MaxShapeLayers`, flags, etc. **Exclude** backing-field duplicates.

---

## Manager / layout import

Decompose `progression_layout.Levels`, `SideUpgrades`, `SideQuests`, `AllUpgrades` into **index/link rows** referencing `node_key` / `upgrade_key` — do not store 1.7 MB JSON on one row.

---

## Anti-patterns rejected

| Rejected | Why |
| -------- | --- |
| `research_unlocks_raw_json` | Forbidden |
| PK = `stable_id` | 168 collisions |
| Model `ResearchUnlockManager` | Runtime type |
| JSONField for `progression_layout` | Normalize |
