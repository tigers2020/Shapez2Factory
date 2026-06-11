# Random Sampling — `toolbar_entries.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | `0 .. 203` |
| Sample size | **3** |
| Selected indices | **`16`**, **`103`**, **`115`** |

```python
random.Random(20260521).sample(range(204), 3)  # [16, 103, 115]
```

---

## Sample A — index 16 (`GroupToolbarElementData`)

```json
{
  "source_type_name": "GroupToolbarElementData",
  "display_name_key": "root/Children[0]/Children[4]",
  "definition_snapshot": {
    "Title": { "$cycle": "Core.Localization.LazyLocalizedText" },
    "Icon": { "$unity": "UnityEngine.Sprite", "name": "…" },
    "SectionIndex": 0,
    "RememberPreferredChild": false,
    "Children": [ "…" ]
  }
}
```

**Interest:** Group folder node in toolbar tree; `Children[]` defines hierarchy (not separate rows until flattened).

---

## Sample B — index 103 (`BuildingBasedPlacementToolbarElementData`)

```json
{
  "display_name_key": "root/Children[3]/Children[2]/Children[2]",
  "definition_snapshot": {
    "EntityType": "Building",
    "IPlacementToolbarElementData.PlacerId": { "Id": 1 },
    "BuildingDefinition": {
      "Id": { "Id": "FluidPortReceiverVariant" },
      "Icon": { "name": "…" },
      "IsTransportBuilding": false,
      "PlayerBuildable": true
    }
  }
}
```

**Interest:** Core planner link — **`BuildingDefinition.Id.Id`** maps to building group/variant; icon name maps to `sprites.json`.

---

## Sample C — index 115 (`IslandBasedPlacementToolbarElementData`)

```json
{
  "display_name_key": "root/Children[5]/Children[3]/Children[0]",
  "definition_snapshot": {
    "EntityType": "Island",
    "IslandGroup": {
      "Id": { "Name": "ShapeMinerExtractorsGroup" }
    },
    "SectionIndex": 0,
    "IPlacementToolbarElementData.PlacerId": { "Id": "…" }
  }
}
```

**Interest:** Island/belt group placement — ties to transport/island simulation naming.

---

## Full-file patterns

| Pattern | Evidence |
| ------- | -------- |
| 204 unique `display_name_key` paths | Tree flattening |
| 204 unique `stable_id` | |
| 57 distinct `BuildingDefinition.Id.Id` | 78 building rows |
| 21 separators | `$type` only |
| File size ~5.7 MB | Nested `BuildingDefinition` / `IslandGroup` payloads |

## Traceability

Samples → `toolbar_element` + `toolbar_group` / `toolbar_building_placement` / `toolbar_island_placement`.
