# Random Sampling — `research_unlocks.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | Indices `0 .. 435` |
| Sample size | **3** |
| Selected indices | **`32`**, **`207`**, **`231`** |

```python
random.Random(20260521).sample(range(436), 3)  # → [32, 207, 231]
```

---

## Sample A — index 32 (`ResearchLevel`)

```json
{
  "source_type_name": "ResearchLevel",
  "stable_id": "a75184142c3595ab…",
  "definition_snapshot": {
    "Id": { "Id": "Milestone_PostFinal_Tier3" },
    "Title": "…",
    "Lines": [
      {
        "Costs": [
          {
            "Amount": 1,
            "ShapeHash": "Yk--Yw--",
            "$type": "ResearchCostShapes"
          }
        ]
      }
    ],
    "RequiredUpgrades": [],
    "Rewards": []
  }
}
```

**Interest:** Milestone ladder with **multi-line** cost structure; `ShapeHash` ties to shape catalog; shares `stable_id` with a paired `ResearchUpgradeId` row.

---

## Sample B — index 207 (`Game.Core.Research.ResearchUpgradeId`)

```json
{
  "source_type_name": "Game.Core.Research.ResearchUpgradeId",
  "stable_id": "…",
  "definition_snapshot": {
    "Id": "SG_Trains_4_2"
  }
}
```

**Interest:** Minimal registry row — canonical key is string **`Id`** only; CLR type name must not become a Django model.

---

## Sample C — index 231 (`Game.Core.Research.ResearchUpgradeId`)

```json
{
  "source_type_name": "Game.Core.Research.ResearchUpgradeId",
  "definition_snapshot": {
    "Id": "SG_Mixing_2_2"
  }
}
```

**Interest:** Another upgrade key in mixing branch; pairs with side-quest / building unlock naming (`SG_*`).

---

## Full-file patterns

| Pattern | Evidence |
| ------- | -------- |
| 188 side quests | `ResearchSideQuest` |
| 168 upgrade id rows | `ResearchUpgradeId` |
| 168 `stable_id` duplicates | Level + UpgradeId pairs |
| `Id` as nested dict | Quest/level/side upgrade |
| Manager singleton | One `progression_layout` with 13 `Levels` |
| 253+ distinct `ShapeHash` in costs | Cross-ref `items.json` |

## Traceability

Samples → `research_milestone`, `research_upgrade` (+ cost rows for sample A).
