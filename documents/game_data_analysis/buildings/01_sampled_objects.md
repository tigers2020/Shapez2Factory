# Random Sampling — `buildings.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | Indices `0 .. 66` |
| Sample size | **3** |
| Method | `random.Random(20260521).sample(range(67), 3)` |
| Selected indices | **`8`**, **`51`**, **`57`** |

## Sampled groups

| Index | `source_guid` | Structural interest |
| ----- | ------------- | ------------------- |
| 8 | `CutterDefaultVariant` | Production machine; `LinePerpendicular`; 2 `Definitions` (1 named + cycle) |
| 51 | `VirtualPainterDefaultVariant` | Virtual building; signal variant; sim stats mostly false |
| 57 | `VirtualCrystalGeneratorDefaultVariant` | Virtual generator; `Single` placement |

---

## Sample A — index 8 (`CutterDefaultVariant`)

```json
{
  "stable_id": "2acbbab463103a0c810701f26116ce45e7716433075085d8114e60da8c94fc9c",
  "source_type_name": "BuildingDefinitionGroup",
  "source_guid": "CutterDefaultVariant",
  "display_name_key": "CutterDefaultVariant",
  "simulation_parameters": {
    "IsTransportBuilding": false,
    "ShowStatBeltProcessingTime": true,
    "ShowStatBuildingsPerFullBelt": true,
    "ShowInSpeedOverview": true,
    "PipetteOverrideId": { "Id": "" }
  },
  "definition_snapshot": {
    "Id": { "Id": "CutterDefaultVariant" },
    "DefaultPreferredPlacementMode": "LinePerpendicular",
    "IsTransportBuilding": false,
    "Definitions": [
      { "Id": { "Name": "CutterDefaultInternalVariant" }, "ConnectorData": { "..." : "..." } }
    ]
  }
}
```

**Note:** Second `Definitions` entry is typically `{"$cycle": "..."}` (omitted).

---

## Sample B — index 51 (`VirtualPainterDefaultVariant`)

```json
{
  "source_guid": "VirtualPainterDefaultVariant",
  "display_name_key": "VirtualPainterDefaultVariant",
  "simulation_parameters": {
    "IsTransportBuilding": false,
    "ShowStatBeltProcessingTime": false,
    "ShowStatBuildingsPerFullBelt": false,
    "ShowInSpeedOverview": true
  },
  "definition_snapshot": {
    "Id": { "Id": "VirtualPainterDefaultVariant" },
    "DefaultPreferredPlacementMode": "Single",
    "Definitions": [
      { "Id": { "Name": "VirtualPainterDefaultInternalVariant" } }
    ]
  }
}
```

---

## Sample C — index 57 (`VirtualCrystalGeneratorDefaultVariant`)

```json
{
  "source_guid": "VirtualCrystalGeneratorDefaultVariant",
  "display_name_key": "VirtualCrystalGeneratorDefaultVariant",
  "definition_snapshot": {
    "Id": { "Id": "VirtualCrystalGeneratorDefaultVariant" },
    "DefaultPreferredPlacementMode": "Single",
    "Definitions": [
      { "Id": { "Name": "VirtualCrystalGeneratorDefaultInternalVariant" } }
    ]
  }
}
```

---

## Full-file patterns

| Pattern | Evidence |
| ------- | -------- |
| `display_name_key == source_guid` | 67/67 |
| Snapshot duplicate of `building_groups.json` | 67/67 byte-equal |
| `stable_id` differs from `building_groups.json` | 0/67 equal |
| `simulation_parameters` matches groups file | 67/67 |
| Transport groups | 12 with `IsTransportBuilding: true` |

## Traceability

Maps to `building`, `building_simulation_setting`, `building_group_member`, `building_placement_rule`.
