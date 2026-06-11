# Random Sampling — `sprites.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | `0 .. 60` |
| Sample size | **3** |
| Selected indices | **`4`**, **`25`**, **`28`** |

```python
random.Random(20260521).sample(range(61), 3)  # [4, 25, 28]
```

---

## Sample A — index 4 (`BeltReaderIcon`)

```json
{
  "stable_id": "302139aefd8dceeea88ae437267ea8b3844af22b15f4f6acb25be38da4345752",
  "source_type_name": "UnityEngine.Object",
  "source_guid": "",
  "source_path": "BeltReaderIcon",
  "display_name_key": "BeltReaderIcon",
  "sprite_path": "BeltReaderIcon"
}
```

**Interest:** Transport/belt UI icon; typical flat envelope.

---

## Sample B — index 25 (`LogicGateCompareIcon`)

```json
{
  "sprite_path": "LogicGateCompareIcon",
  "source_path": "LogicGateCompareIcon",
  "display_name_key": "LogicGateCompareIcon",
  "source_type_name": "UnityEngine.Object",
  "source_guid": ""
}
```

**Interest:** Logic-gate family icon — ties to `LogicGate*` building variants by naming.

---

## Sample C — index 28 (`LogicGateOrIcon`)

```json
{
  "sprite_path": "LogicGateOrIcon",
  "display_name_key": "LogicGateOrIcon",
  "source_type_name": "UnityEngine.Object"
}
```

**Interest:** Sibling logic icon; same schema as samples A/B.

---

## Full-file patterns

| Pattern | Evidence |
| ------- | -------- |
| Triple path equality | 61/61 |
| Unique `stable_id` | 61/61 |
| Meta registry coverage | 61 sprite refs resolve |
| No texture/atlas data in JSON | paths only |

## Traceability

Samples → `sprite_asset` rows + matching `asset_meta_reference` (sprite).
