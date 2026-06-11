# Random Sampling — `belts_pipes_transport.json`

## Sampling parameters

| Parameter | Value |
| --------- | ----- |
| Random seed | **`20260521`** |
| Population | Array indices `0 .. 8` (9 elements) |
| Sample size | **3** |
| Method | `random.Random(20260521).sample(range(9), 3)` |
| Selected indices | **`1`**, **`3`**, **`6`** |

## Sampled groups

| Index | `transport_kind` | Why structurally interesting |
| ----- | ---------------- | ---------------------------- |
| 1 | `BeltPortSender` | Mixed IO: item input + `BeltPortOutput`; legacy `BeltPortOutput` map |
| 3 | `FluidPortSender` | Single `BuildingFluidInput`, `IOType: Pipe` |
| 6 | `WireForward` | Dual `BuildingSignalJunction`, `IOType: Wire`, signal legacy graph |

---

## Sample 1 — index 1 (`BeltPortSender`)

```json
{
  "stable_id": "7c7fe7e887a0516373a045fb0c7f6a48b8dca43606e97b318a3a0d7f495e196b",
  "source_type_name": "BuildingDefinition",
  "source_guid": "BeltPortSender",
  "source_path": "",
  "display_name_key": "BeltPortSender",
  "transport_kind": "BeltPortSender",
  "definition_snapshot": {
    "Id": { "Name": "BeltPortSenderInternalVariant" },
    "ConnectorData": {
      "AllBuildingConnectors": [
        {
          "TileDirection": { "Value": "West" },
          "IOType": "ElevatedBorder",
          "StandType": "Normal",
          "$type": "BuildingItemInput"
        },
        {
          "TileDirection": { "Value": "East" },
          "IOType": "None",
          "StandType": "None",
          "$type": "BeltPortOutput"
        }
      ],
      "TileDimensions": { "x": 1, "y": 1, "z": 1 }
    }
  }
}
```

**Linked variant:** `BeltPortSenderInternalVariant` in `building_variants.json` (snapshot **identical**).

---

## Sample 2 — index 3 (`FluidPortSender`)

```json
{
  "stable_id": "fdabac323dfaeb754f898f93fec1a93aebfa46da983c5b0d86ca876efc48777b",
  "transport_kind": "FluidPortSender",
  "definition_snapshot": {
    "Id": { "Name": "FluidPortSenderInternalVariant" },
    "ConnectorData": {
      "AllBuildingConnectors": [
        {
          "IOType": "Pipe",
          "TileDirection": { "Value": "West" },
          "$type": "BuildingFluidInput"
        }
      ],
      "TileDimensions": { "x": 1, "y": 1, "z": 1 }
    }
  }
}
```

**Pattern:** single-port fluid sender; `_IOType` duplicate field observed in full snapshot (review).

---

## Sample 3 — index 6 (`WireForward`)

```json
{
  "stable_id": "1c4cb5c84b43ae050b8f8837ecc07eddd1cae115e302bf400948880c5e3fa909",
  "transport_kind": "WireForward",
  "definition_snapshot": {
    "Id": { "Name": "WireDefaultForwardInternalVariant" },
    "ConnectorData": {
      "AllBuildingConnectors": [
        {
          "IOType": "Wire",
          "TileDirection": { "Value": "West" },
          "$type": "BuildingSignalJunction"
        },
        {
          "IOType": "Wire",
          "TileDirection": { "Value": "East" },
          "$type": "BuildingSignalJunction"
        }
      ],
      "TileDimensions": { "x": 1, "y": 1, "z": 1 }
    }
  }
}
```

**Pattern:** wire transport uses signal junction connectors, not item/fluid ports.

---

## Full-file patterns (beyond samples)

| Pattern | Evidence |
| ------- | -------- |
| Snapshot duplication | 9/9 `definition_snapshot` equals `building_variants.json` counterpart |
| Distinct transport IDs | 9/9 `stable_id` ≠ variant `stable_id` for same `Id.Name` |
| Footprint | All records 1×1×1 tile |
| Connector count | 2 for belt/pipe/wire forward; 1 for port/transmitter variants |
| `display_name_key` | Always equals `transport_kind` |

## Traceability

Samples map to `transport_building_registry` + shared `building_variant` / `building_connector` schema (see `03_reconstructed_schema.md`).
