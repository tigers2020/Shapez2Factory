---
title: Space Transport System (Belt & Pipeline)
created: 2026-06-11
updated: 2026-06-11
type: concept
tags: [transport, game-data-analysis]
sources: [raw/analysis/belts_pipes_transport/00_summary.md, raw/articles/space-transport-identifiers.md]
confidence: high
---

# Space Transport System

## Source
`documents/game_data/belts_pipes_transport.json` — 365 KB, SHA256 `e864...`. Unity v2 runtime_reflection dump.

## Structure
- **9 top-level objects** (homogeneous envelope + nested snapshots)
- 54 layout identifiers: SpaceBelt_* (27) + SpacePipe_* (27)
- Layout types: Forward, Left/Right Turn, Merger, Splitter, Y-mixer, Triple-merger, Lift1/Lift2 × Up/Down × Direction

## Capacity Reference
| Transport | Base Rate | Max (×16) | Notes |
|-----------|-----------|-----------|-------|
| Miner | 30 shapes/m | 480 | Base source for shapes |
| Pump | 300 L/m | 4.8 kL | Base source for fluids |
| Space Belt | 5,760 shapes/m | — | Absolute bottleneck |
| Space Pipeline | 345.6 kL/m | — | Fluid absolute bottleneck |

## Cell Kind Classification
- `SpaceBelt_*` → `cell_kind: space_belt` (shaped items)
- `SpacePipe_*` → `cell_kind: space_pipe` (fluids only)

## Cross-References
- [[building-definitions]]: corridor buildings reference these layouts
- [[asteroid-lab-algorithm]]: routing layer uses transport capacity planning
- [[game-data-manifest]]: Unity runtime reflection dump surface

## Design Notes
Transport identifiers define the layout primitives for Space Belt and Space Pipe corridors on asteroid labs. Routing algorithms must respect Lift1/Lift2 level transitions between rim layers. ^[raw/analysis/belts_pipes_transport/00_summary.md]
