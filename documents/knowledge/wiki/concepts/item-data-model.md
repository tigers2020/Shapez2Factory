---
title: Item Data Model (Shape Recipes)
created: 2026-06-11
updated: 2026-06-11
type: concept
tags: [game-data-analysis, shape-algebra]
sources: [raw/analysis/items/00_summary.md]
confidence: high
---

# Item Data Model

## Source
`documents/game_data/items.json` — 83 KB, SHA256 `3d1e...`. Unity runtime_reflection dump.

## Structure
- **70 item definitions** — gameplay subset of the full shape catalog
- Nested: `Definition → Layers[] → Parts[] → Shape/Color`
- `stable_id`: all 70 share same hash (import artifact, not domain key)
- `display_name_key`: constant "ShapeItem"

## Relationship to Shapes
All 70 item Hash values are a **subset** of the 1,170 entries in [[shape-data-model]]. 
- Items = gameplay-relevant shapes used as research deliverables / factory targets
- Shapes.json = authoritative full catalog; items.json = optional subset

## Cross-References
- [[shape-data-model]]: superset of all possible shapes
- [[research-unlocks]]: research tree references these item hashes
- [[item-data-model]]: normalized model uses shape_recipe + layer + quadrant_slot
