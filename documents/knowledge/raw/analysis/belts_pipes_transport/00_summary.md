# File Inventory — `belts_pipes_transport.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/belts_pipes_transport.json` |
| File name | `belts_pipes_transport.json` |
| Manifest hash | `sha256:e864a179ef4fb12450ad452ae933d896024bec99a2a1810b4b06e25a13c95a54` |
| Approx. size | 365,552 bytes |
| Dump context | `manifest.json` → `source_method: runtime_reflection`, v2 export includes transport captures |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **9** |
| Element type | **object** (homogeneous envelope + large nested snapshot) |
| Max nesting depth | **~8** (under `definition_snapshot`) |

No top-level object keys (root is an array).

## Major object groups

Logical groups = **one transport definition per array element** (9 total):

| Group (`transport_kind`) | Category (inferred) | Internal variant (`definition_snapshot.Id.Name`) |
| ------------------------ | ------------------- | ------------------------------------------------ |
| `ForwardBelt` | belt | `BeltDefaultForwardInternalVariant` |
| `BeltPortSender` | belt_port | `BeltPortSenderInternalVariant` |
| `BeltPortReceiver` | belt_port | `BeltPortReceiverInternalVariant` |
| `FluidPortSender` | fluid_port | `FluidPortSenderInternalVariant` |
| `FluidPortReceiver` | fluid_port | `FluidPortReceiverInternalVariant` |
| `PipeForward` | pipe | `PipeForwardInternalVariant` |
| `WireForward` | wire | `WireDefaultForwardInternalVariant` |
| `WireTransmitterSender` | signal_port | `WireTransmitterSenderInternalVariant` |
| `WireTransmitterReceiver` | signal_port | `WireTransmitterReceiverInternalVariant` |

## Envelope fields (9/9 each)

| Field | Type | Notes |
| ----- | ---- | ----- |
| `stable_id` | 64-char hex | Transport-registry ID (≠ variant `stable_id`) |
| `transport_kind` | string | Planner/simulation-facing kind label |
| `display_name_key` | string | Equals `transport_kind` in all rows |
| `source_guid` | string | Equals `transport_kind` |
| `source_path` | string | Always `""` |
| `source_type_name` | string | Always `BuildingDefinition` (dump label) |
| `definition_snapshot` | object | Large nested building definition graph |

## Repeated structures (inside `definition_snapshot`)

| Structure | Occurrences | Role |
| --------- | ----------- | ---- |
| `ConnectorData.AllBuildingConnectors[]` | 9–18 connectors total | Directional IO endpoints |
| `ConnectorData.Tiles[]` | 9 tiles (1×1 each) | Footprint occupancy |
| `ConnectorData.LegacyBuildingIOMap.*` | Per-variant slots | Legacy/cycle-linked IO graph |
| `CustomData` / `IEntityDefinition.CustomData` | 9 | Simulation/rendering config blobs |
| `Id.Name` | 9 | Internal variant name (links `building_variants.json`) |
| Generic keys `IEntityConnectorData<...>.AllConnectors` | 9 | **Runtime/reflection** duplicate of connectors |
| `<*k__BackingField>` keys | ~731 key instances | **Runtime/reflection** — exclude from domain |

## Arrays detected

| Path | Typical length |
| ---- | -------------- |
| `$` (root) | 9 |
| `[*].definition_snapshot.ConnectorData.AllBuildingConnectors` | 1–2 |
| `[*].definition_snapshot.ConnectorData.Tiles` | 1 |
| `[*].definition_snapshot.CustomData.All` | ~10 per record |
| `[*].definition_snapshot.ConnectorData.LegacyBuildingIOMap.*` | 0–2 (often empty arrays) |

## Nested objects

Heavy nesting under `definition_snapshot` (building definition graph: connectors, custom simulation, rendering, localization placeholders, Unity mesh references).

**Critical finding (full-file):** For all 9 rows, `definition_snapshot` JSON is **byte-identical** to the matching row in `building_variants.json` (same `Id.Name`). This file adds a **transport envelope** with distinct `stable_id` and `transport_kind`.

## Candidate IDs

| Field | Uniqueness | Role |
| ----- | ---------- | ---- |
| `stable_id` | 9 unique | Transport registry PK |
| `transport_kind` | 9 unique | Natural planner key |
| `definition_snapshot.Id.Name` | 9 unique | FK lookup to `building_variant.internal_name` |
| `ref_stable_id` | N/A | Not present |

## Runtime / reflection / debug strings

| Pattern | Count / presence | Classification |
| ------- | ---------------- | -------------- |
| `source_type_name: BuildingDefinition` | 9 | Source metadata (dump type label) |
| `<Field>k__BackingField` keys | ~731 | Runtime/reflection |
| `IEntityConnectorData<Game.Core.Coordinates...>.AllConnectors` | 9 | Runtime/reflection duplicate |
| `$type` discriminator strings | 60 distinct types | Serializer metadata (map to domain enums, not table names) |
| `Game.Content.*`, `Core.Localization.*`, `System.Reflection.*`, `UnityEngine.*` in `$type` | Many | Runtime/reflection / engine types |
| `$cycle` references in LegacyBuildingIOMap | Present | Dump graph cycles — not domain IDs |

**No** `Version=0.0.0.0` / `PublicKeyToken` strings in this file.

## Possible source metadata

- Empty `source_path` (9/9)
- `source_type_name` / `$type` / `$unity` (if present in deeper nodes)
- `manifest` dump headers and `file_hashes`

## Cross-file inventory (full corpus)

| Target file | Relationship |
| ----------- | ------------ |
| `building_variants.json` | 9/9 snapshots **identical** by `Id.Name`; variant `stable_id` differs from transport `stable_id` |
| `buildings.json` | 12 `IsTransportBuilding` groups; **0** direct `source_guid` match to transport kinds |
| `toolbar_entries.json` | Mentions 7/9 `transport_kind` strings (not `ForwardBelt` / `WireForward` in grep sample) |
| `simulation_systems.json` | Mentions all 9 `transport_kind` strings |

## Design implication

Treat this file primarily as **`transport_building_registry`** (9 rows) pointing at **`building_variant`** geometry/simulation data — **do not** persist another copy of the full snapshot as primary storage.
