# Game data dump (`documents/knowledge/raw/game_data`)

Runtime-reflection JSON export of Shapez 2 game definitions. Integrity: `manifest.json` (`file_hashes`, `incomplete_sections`).

**Path resolution:** `python manage.py import_game_data` auto-resolves the bundle directory via `bundle_gate` — tries `documents/game_data`, then this directory (`documents/knowledge/raw/game_data`). Override with `--source /path/to/bundle`.

## JSON artifacts

| File | Contents (short) |
| ---- | ---------------- |
| `buildings.json` | Building definition snapshots |
| `building_groups.json` | Building groups |
| `building_variants.json` | Variant snapshots |
| `belts_pipes_transport.json` | Factory transport registry (`ForwardBelt`, ports, …) |
| `toolbar_entries.json` | Toolbar tree |
| `research_unlocks.json` | Research / island definitions / wiki |
| `simulation_systems.json` | Simulation system snapshots |
| `raw_type_index.json` | CLR type index |
| `sprites.json`, `prefabs.json`, `materials.json`, `items.json`, `shapes.json`, `fluids.json` | Asset / content slices |
| `asset_references.json` | Asset cross-refs |
| `translations.json` | Translation slice (sparse vs embedded LazyText) |

## Import

```bash
# Auto-resolve bundle path, validate hashes (fail-closed), import ORM
python manage.py import_game_data

# Custom bundle directory
python manage.py import_game_data --source /path/to/bundle

# Disk validate + reconcile with latest ImportBatch (no import)
python manage.py import_game_data --verify
```

Contract: [`documents/architecture/game-data-import-boundary/spec.md`](../../../architecture/game-data-import-boundary/spec.md).

## Topic guides

| Doc | Topic |
| --- | ----- |
| [`space_transport_identifiers.md`](space_transport_identifiers.md) | Island `SpaceBelt_*` / `SpacePipe_*` ids, groups, JSON paths, lab mapping |
| [`../game_data_analysis/`](../game_data_analysis/) | Per-artifact schema, import mapping, validation plans |
