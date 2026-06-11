---
title: Fluid Data Model
created: 2026-06-11
updated: 2026-06-11
type: concept
tags: [fluids, game-data-analysis]
sources: [raw/analysis/fluids/00_summary.md]
confidence: high
---

# Fluid Data Model

## Source
`documents/game_data/fluids.json` — 2,749 bytes, SHA256 `8a9b...`. Unity runtime_reflection dump.

## Structure
- **9 fluid definitions** in the dump envelope
- Only `definition_snapshot.Color.name` and `instance_id` differ across entries
- Color palette: RGB primary colors + secondary mixtures derived from Mixer building

## Key Constraint
Only RGB primary colors are selectable at source (Pump). Secondary colors must be produced via Mixer building.

## Cross-References
- [[shape-data-model]]: shape quadrants share the same `MetaShapeColor` enum for painting operations
- [[building-definitions]]: Pump and Mixer buildings reference these fluids
- [[transport-system]]: Space Pipes carry fluids; pump throughput is 300 L/m base

## Design Notes
Fluids are a small but critical dataset. The color system is shared between shapes (paint operation) and fluids — unified RGB palette. ^[raw/analysis/fluids/00_summary.md]
