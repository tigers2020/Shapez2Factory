# Game data dump (`documents/game_data`)

Runtime-reflection JSON export of Shapez 2 game definitions. Integrity hashes and versions: `manifest.json`.

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

Import into Django: `python manage.py import_game_data` (see [`documents/ai/manuals/django.md`](../ai/manuals/django.md)).

## Topic guides

| Doc | Topic |
| --- | ----- |
| [`space_transport_identifiers.md`](space_transport_identifiers.md) | Island `SpaceBelt_*` / `SpacePipe_*` ids, groups, JSON paths, lab mapping |
| [`../game_data_analysis/`](../game_data_analysis/) | Per-artifact schema, import mapping, validation plans |
