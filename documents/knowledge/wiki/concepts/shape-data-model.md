---
title: Shape Data Model
created: 2026-06-11
updated: 2026-06-12
type: concept
tags: [shape-algebra, game-data-analysis]
sources: [raw/analysis/shapes/00_summary.md]
confidence: high
---

# Shape Data Model

## Source
`documents/game_data/shapes.json` — 1,728 bytes, manifest SHA256 `bee0de...`. Dumped via Unity runtime_reflection v2.

## Structure
- **Array of 1,170 shape recipes** — full catalog of all possible shapes
- Each element: `stable_id`, `source_*`, `display_name_key` (`#1`…`#1170`), `definition_snapshot`, `simulation_parameters`
- `definition_snapshot` fields: `UniqueOperationId` (int, 1–1330, 160 gaps), `PartCount` (always **4**), `Layers[]` (1–4 layers), `Parts[]` per layer, `Hash` (unique string)

## Layer/Quadrant Model
- Every shape has exactly **4 quadrant slots** (`PartCount=4`)
- Layers: 1 to 4 per recipe (~500+ are single-layer, rest multi-layer)
- Each quadrant: `Shape` (kind letter: C=Sircle, R=Rectangle, S=Spike, W=Diamond) + `Color` (RGB palette)
- ~11,000+ total part records across all recipes

## Keys
| Field | Use | Notes |
|-------|-----|-------|
| `Hash` | Primary business key | Planner / research cost lookup |
| `UniqueOperationId` | Numeric ID | 1–1330 with gaps |
| `stable_id` | Import correlation | Unique within shapes.json |

## Cross-References
- [[materials-data-model]]: quadrant `Shape` letter codes (C/R/S/W/c/P/-)
- [[item-data-model]]: items.json contains 70 shape items whose `Hash` values ⊆ shapes (subset)
- [[research-unlocks]]: 253 `ShapeHash` references all resolve to shapes catalog
- [[game-data-manifest]]: Unity runtime reflection dump surface

## Design Notes
Use normalized model: shape_recipe → shape_recipe_layer → shape_quadrant_slot. Shapes.json is authoritative; items.json is gameplay subset. Do NOT duplicate as JSONField tables. ^[raw/analysis/shapes/00_summary.md]
