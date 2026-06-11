---
title: Building Definitions
created: 2026-06-11
updated: 2026-06-11
type: concept
tags: [buildings, game-data-analysis]
sources: [raw/analysis/buildings/00_summary.md]
confidence: high
---

# Building Definitions

## Source
`documents/game_data/buildings.json` — ~13 MB, SHA256 `907bfc...`. Unity runtime_reflection v2 dump.

## Structure
- **Array of 67 building definition groups** — each representing a player-placeable building type
- Nested structure: `definition_snapshot` → building variant snapshots → factory inputs/outputs → transport adapters
- Max nesting depth ~8+ levels under `definition_snapshot`

## Key Building Categories
Buildings include miners, pumps, cutters, stackers, swappers, painters, pinners, crystal feeders, exporters, corridors (belts/pipes), and asteroid connectors.

## Cross-References
- [[building-groups]]: building_groups.json defines logical groupings of related buildings
- [[building-variants]]: building_variants.json holds parameterized variant data
- [[transport-capacity]]: corridor buildings link to belt/pipe transport specs
- [[prefabs]]: prefab definitions reference building types

## Design Notes
Buildings are the largest game data file by size (13 MB) due to deep nesting. Each building carries factory I/O definitions, sprite references, and simulation parameters. ^[raw/analysis/buildings/00_summary.md]
