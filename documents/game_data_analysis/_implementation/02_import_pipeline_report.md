# Import Pipeline Report

## Command

```bash
python manage.py import_game_data --source documents/game_data --batch-name <name>
```

## Pipeline steps

1. Load `manifest.json` → `ImportBatch`, checksums, warnings, incomplete sections
2. `fluids.json` → `FluidColor`
3. `shapes.json` → `ShapeRecipe` tree (`catalog_source=full`)
4. `items.json` → upsert subset (`catalog_source=items`)
5. `building_variants.json` → `BuildingVariant`, connectors, tiles
6. `buildings.json` → `BuildingGroup` (`display_profile=plain`)
7. `building_groups.json` → `BuildingGroup` (`display_profile=lazy_overlay`)
8. `prefabs.json` / `sprites.json` / `materials.json` → `GameContentAsset`
9. `asset_references.json` → `AssetMetaReference` (requires content assets)
10. `research_unlocks.json` → research tables + costs
11. `simulation_systems.json` → `SimulationSystem` (C-lite), `SimulationClrProvenance`, connectable children, belt policy
12. `toolbar_entries.json` → toolbar tables + FK to variants
13. `translations.json` → `LocalizationExportStatus` only
14. `belts_pipes_transport.json` → `TransportBuildingRegistry` (no variant duplicate)
15. `raw_type_index.json` → `ClrTypeRegistryEntry`

## Idempotency

- Upsert by global `canonical_id` (and natural keys where noted).
- `ImportBatch` keyed by `manifest_self_hash`.
- Re-run yields identical row counts and FK graph for same source directory.

## Unknown fields

Captured via `UnknownProperty` helper in `ImportContext.record_unknown` (not yet wired to every handler — extend per new JSON keys).

## Typical counts (this dump)

| Entity | Approx. rows |
| ------ | ------------ |
| `FluidColor` | 9 |
| `ShapeRecipe` | 1170 (+ items overlap) |
| `BuildingVariant` | 131 |
| `GameContentAsset` | 829 |
| `ClrTypeRegistryEntry` | 6497 |
| `ToolbarElement` | 204 |

## Warnings

- `translations.json` empty — no `LocalizedMessage` rows.
- Large files (`simulation_systems`, `toolbar_entries`) import without storing raw JSON blobs.
