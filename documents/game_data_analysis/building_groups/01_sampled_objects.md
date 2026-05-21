# Random Sampling — `building_groups.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | Array indices `0 .. 66` (67 elements) |
| Sample size | **3** |
| Method | `random.Random(20260521).sample(range(67), 3)` |
| Selected indices | **`8`**, **`51`**, **`57`** |

## Sampled groups

| Index | `source_guid` | Structural interest |
| ----- | ------------- | ------------------- |
| 8 | `CutterDefaultVariant` | Production building; 2 embedded defs + cycle refs; `LinePerpendicular` placement |
| 51 | `VirtualPainterDefaultVariant` | Virtual building; signal IO connectors; stats flags mostly false |
| 57 | `VirtualCrystalGeneratorDefaultVariant` | Virtual generator; similar signal topology; `Single` placement |

---

## Sample A — index 8 (`CutterDefaultVariant`)

```json
{
  "stable_id": "60f8d1c63923c9dc3499f54fde347845211c2f9783e330dde8bc1e04d6347e6f",
  "source_type_name": "BuildingDefinitionGroup",
  "source_guid": "CutterDefaultVariant",
  "display_name_key": "LazyText[building-variant.CutterDefaultVariant.title]",
  "description_key": "LazyText[building-variant.CutterDefaultVariant.description]",
  "simulation_parameters": {
    "IsTransportBuilding": false,
    "PipetteOverrideId": { "Id": "" },
    "ShowStatBeltProcessingTime": true,
    "ShowStatBuildingsPerFullBelt": true,
    "ShowInSpeedOverview": true
  },
  "definition_snapshot": {
    "Id": { "Id": "CutterDefaultVariant" },
    "DefaultPreferredPlacementMode": "LinePerpendicular",
    "IsTransportBuilding": false,
    "Definitions": [
      {
        "Id": { "Name": "CutterDefaultInternalVariant" },
        "ConnectorData": {
          "AllBuildingConnectors": [
            { "TileDirection": { "Value": "West" }, "IOType": "Regular", "$type": "BuildingItemInput" },
            { "TileDirection": { "Value": "East" }, "IOType": "Regular", "$type": "BuildingItemOutput" }
          ]
        }
      }
    ]
  }
}
```

**Note:** Full group has 2 `Definitions` entries; excerpt shows first embedded variant. Second member may be `{"$cycle": "..."}` in complete file.

---

## Sample B — index 51 (`VirtualPainterDefaultVariant`)

```json
{
  "source_guid": "VirtualPainterDefaultVariant",
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
      {
        "Id": { "Name": "VirtualPainterDefaultInternalVariant" },
        "ConnectorData": {
          "AllBuildingConnectors": [
            { "$type": "BuildingSignalOutput", "IOType": "Building", "TileDirection": { "Value": "East" } },
            { "$type": "BuildingSignalInput", "IOType": "Building", "TileDirection": { "Value": "West" } }
          ]
        }
      }
    ]
  }
}
```

**Pattern:** virtual buildings use signal input/output, not belt item ports.

---

## Sample C — index 57 (`VirtualCrystalGeneratorDefaultVariant`)

```json
{
  "source_guid": "VirtualCrystalGeneratorDefaultVariant",
  "definition_snapshot": {
    "Id": { "Id": "VirtualCrystalGeneratorDefaultVariant" },
    "DefaultPreferredPlacementMode": "Single",
    "Definitions": [
      {
        "Id": { "Name": "VirtualCrystalGeneratorDefaultInternalVariant" },
        "ConnectorData": {
          "AllBuildingConnectors": [
            { "$type": "BuildingSignalOutput", "IOType": "Building", "TileDirection": { "Value": "East" } },
            { "$type": "BuildingSignalInput", "IOType": "Building", "TileDirection": { "Value": "West" } }
          ]
        }
      }
    ]
  }
}
```

---

## Full-file patterns (beyond samples)

| Pattern | Evidence |
| ------- | -------- |
| Snapshot = `buildings.json` | 67/67 byte-equal `definition_snapshot` by `source_guid` |
| Group `stable_id` ≠ building `stable_id` | 0/67 equal hashes |
| LazyText keys | 67/67 `display_name_key` + `description_key` parse to `building-variant.<Id>.{title\|description}` |
| Member count | 131 `Definitions` = 131 `building_variants.json` rows |
| Cycle members | 34 definitions are `$cycle`-only (no `Id.Name`) |
| Placement modes | `CodeOverriden` (19), `LinePerpendicular` (18), `Single` (17), `Area` (11), … |

## Traceability

Samples map to `building_group` + `building_group_member` + `building_group_simulation_setting` (see `03_reconstructed_schema.md`).
