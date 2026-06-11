# Random Sampling — `building_variants.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | Array indices `0 .. 130` (131 elements) |
| Sample size | **3** |
| Method | `random.Random(20260521).sample(range(131), 3)` |
| Selected indices | **`16`**, **`103`**, **`115`** |

## Sampled groups

| Index | `Id.Name` | Structural interest |
| ----- | --------- | ------------------- |
| 16 | `DisplayDefaultInternalVariant` | Single signal input; 1×1×1; display family |
| 103 | `VirtualUnstackerDefaultInternalVariant` | 3 signal outputs + 1 input; multi-direction ports |
| 115 | `WireDefault1UpForwardInternalVariant` | 2-tile vertical wire (`z: 0` and `z: 1`); 1×1×2 footprint |

---

## Sample A — index 16 (`DisplayDefaultInternalVariant`)

```json
{
  "stable_id": "14caf0b16cd3d2e22ebde550516a7b2bfabb996ad0a310ff20ae189aca562b8e",
  "source_type_name": "BuildingDefinition",
  "source_guid": "DisplayDefaultInternalVariant",
  "display_name_key": "DisplayDefaultInternalVariant",
  "building_stable_id": "",
  "definition_snapshot": {
    "Id": { "Name": "DisplayDefaultInternalVariant" },
    "ConnectorData": {
      "AllBuildingConnectors": [
        {
          "IOType": "Building",
          "TileDirection": { "Value": "West" },
          "$type": "BuildingSignalInput"
        }
      ],
      "TileDimensions": { "x": 1, "y": 1, "z": 1 },
      "Tiles": [{ "x": 0, "y": 0, "z": 0 }]
    }
  }
}
```

---

## Sample B — index 103 (`VirtualUnstackerDefaultInternalVariant`)

```json
{
  "source_guid": "VirtualUnstackerDefaultInternalVariant",
  "definition_snapshot": {
    "Id": { "Name": "VirtualUnstackerDefaultInternalVariant" },
    "ConnectorData": {
      "AllBuildingConnectors": [
        { "$type": "BuildingSignalOutput", "TileDirection": { "Value": "East" }, "IOType": "Building" },
        { "$type": "BuildingSignalOutput", "TileDirection": { "Value": "North" }, "IOType": "Building" },
        { "$type": "BuildingSignalInput", "TileDirection": { "Value": "West" }, "IOType": "Building" }
      ],
      "TileDimensions": { "x": 1, "y": 1, "z": 1 },
      "Tiles": [{ "x": 0, "y": 0, "z": 0 }]
    }
  }
}
```

**Pattern:** virtual machine variants use signal IO, not belt item ports.

---

## Sample C — index 115 (`WireDefault1UpForwardInternalVariant`)

```json
{
  "source_guid": "WireDefault1UpForwardInternalVariant",
  "definition_snapshot": {
    "Id": { "Name": "WireDefault1UpForwardInternalVariant" },
    "ConnectorData": {
      "AllBuildingConnectors": [
        {
          "$type": "BuildingSignalJunction",
          "IOType": "Wire",
          "TileDirection": { "Value": "West" },
          "Position_L": { "x": 0, "y": 0, "z": 0 }
        },
        {
          "$type": "BuildingSignalJunction",
          "IOType": "Wire",
          "TileDirection": { "Value": "East" },
          "Position_L": { "x": 0, "y": 0, "z": 1 }
        }
      ],
      "TileDimensions": { "x": 1, "y": 1, "z": 2 },
      "Tiles": [{ "x": 0, "y": 0, "z": 0 }, { "x": 0, "y": 0, "z": 1 }]
    }
  }
}
```

**Pattern:** multi-tile footprint with connectors at different `Position_L.z`.

---

## Full-file patterns (beyond samples)

| Pattern | Evidence |
| ------- | -------- |
| `source_guid == Id.Name` | 131/131 |
| `building_stable_id` empty | 131/131 |
| Tile footprint modes | Mostly 1×1×1 (74); also 1×1×2 (19), 1×1×3 (16), 3×3×3 (5), … |
| IOType usage | `Building` (114), `ElevatedBorder` (80), `Regular` (41), `Pipe` (36), `Wire` (33) |
| Mirrored variants | 34 names end with `Mirrored`; group embed uses `$cycle` instead of full embed |
| Group embed vs variant file | Same `Id.Name` but embed often **smaller JSON** (partial graph) — variant file is authoritative |
| `LabelDefaultInternalVariant` | 0 connectors — edge case |

## Traceability

Samples → `building_variant`, `building_connector`, `building_footprint_tile` (see `03_reconstructed_schema.md`).
