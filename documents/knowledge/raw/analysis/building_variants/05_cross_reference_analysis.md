# Cross-Reference Analysis — `building_variants.json`

## FK relationships (outbound / resolved)

| From | To | Cardinality | Evidence |
| ---- | -- | ----------- | -------- |
| `building_group_member.building_variant_id` | `building_variant` | 131 members → 131 variants | 97 by embedded name + 34 cycle→mirrored |
| `belts_pipes_transport` snapshot `Id.Name` | `building_variant.internal_name` | 9 : 1 | Snapshot byte-equal for 9 transport kinds |
| `simulation_systems.json` | textual reference | 131/131 names | FK schema TBD |
| `research_unlocks.json` | textual reference | 128/131 names | FK schema TBD |

## FK relationships (unresolved in bundle)

| Field | Status |
| ----- | ------ |
| `building_stable_id` | **Empty 131/131** — no parent building hash populated |
| `building_variant` → `buildings.json` `stable_id` | **0 overlap** |
| `building_variant.stable_id` → `prefabs.json` | Not direct; via transport/prefab layer |

## M2M relationships

```text
building_group
  └─ M2M via building_group_member → building_variant (ordered)
```

One variant may appear in one group's `Definitions[]` list; mirrored variants often referenced only via `$cycle` from sibling member.

## Ordered child relationships

```text
building_variant
  ├─ has many → building_connector (AllBuildingConnectors[] order)
  └─ has many → building_footprint_tile (Tiles[] order)
```

## Inferred references by name

| Variant family | Example `internal_name` | Group `source_guid` (examples) |
| -------------- | ----------------------- | ------------------------------ |
| Belt forward | `BeltDefaultForwardInternalVariant` | `BeltDefaultVariant` |
| Mirrored belt | `BeltDefaultLeftInternalVariantMirrored` | (cycle from group) |
| Wire 1-up | `WireDefault1UpForwardInternalVariant` | `WireDefaultVariant` |
| Virtual | `VirtualUnstackerDefaultInternalVariant` | `VirtualUnstackerDefaultVariant` |

## Partial embed vs canonical file

| Source | Snapshot completeness |
| ------ | --------------------- |
| `building_variants.json` | **Full** (~3.8 MB total; per-variant up to ~50KB) |
| `building_groups.json` embedded `Definitions[]` | Often **partial** (smaller JSON for same `Id.Name`) |
| `belts_pipes_transport.json` | **Equal** to variant file for 9 rows |

**Rule:** Treat **this file** as canonical for connector/tile import.

## Unresolved references

| Reference | Notes |
| --------- | ----- |
| Parent `building_group` via `building_stable_id` | Use `building_group_member` import instead |
| `translations.json` for display keys | Manifest: translations incomplete |
| CustomData simulation nodes | Not mapped to relational schema yet |
| `LabelDefaultInternalVariant` | 0 connectors — gameplay role unclear |

## Relationship diagram

```text
game_data_import_batch
  └─ has many → building_variant (131)
        ├─ has many → building_connector (~314 total)
        └─ has many → building_footprint_tile (~150+ tiles)

building_group
  └─ has many → building_group_member (131 slots)
        └─ references → building_variant (internal_name / cycle resolve)

transport_building_registry (belts_pipes_transport)
  └─ references → building_variant (9 internal names, full snapshot match)

simulation_system
  └─ (textual) uses → building_variant.internal_name

research_unlock
  └─ (textual) uses → building_variant.internal_name (128/131)
```

## Cardinality proof

| Metric | Value |
| ------ | ----- |
| Variants | 131 |
| Unique `internal_name` | 131 |
| Unique `stable_id` | 131 |
| Total connectors (sum of list lengths) | 314 (approx from distribution) |
| Mirrored variants | 34 |
