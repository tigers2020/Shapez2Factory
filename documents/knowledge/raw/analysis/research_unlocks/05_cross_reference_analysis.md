# Cross-Reference Analysis — `research_unlocks.json`

## Relationship diagram

```text
game_data_import_batch
  └─ has many → research_upgrade / research_milestone / research_side_quest / …

research_milestone
  ├─ has many → research_milestone_line
  │     └─ has many → research_unlock_cost
  ├─ has many → research_unlock_reward
  └─ has many → research_prerequisite
        ├─ requires → research_upgrade
        └─ requires → research_mechanic

research_side_quest
  ├─ has many → research_unlock_cost
  ├─ has many → research_unlock_reward
  └─ has many → research_prerequisite

research_unlock_cost
  └─ shape_hash → shape_recipe (items.json Hash)

ResearchUnlockManager.progression_layout
  ├─ indexes → research_milestone (Levels)
  ├─ indexes → research_side_upgrade (SideUpgrades)
  └─ indexes → research_side_quest (SideQuests)

research_upgrade (upgrade_key)
  └─ inferred unlocks → building_group / toolbar (by naming convention — no JSON FK)
```

## FK / M2M

| From | To | Resolution |
| ---- | -- | ------------ |
| `research_unlock_cost` | `shape_recipe` | `ShapeHash` |
| `research_prerequisite` | `research_upgrade` | upgrade key string |
| `research_prerequisite` | `research_mechanic` | mechanic id |
| Layout index rows | node tables | `node_key` / `upgrade_key` |

## Unresolved

- Upgrade key → `building_groups` variant (string convention only)
- Rewards → concrete game entities (points vs buildings)
- Translated titles (`translations.json` empty)

## Source metadata

- `stable_id` pairs (level + upgrade id)
- `manager_snapshot`, backing fields, `$type`
