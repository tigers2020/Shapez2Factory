---
title: Materials Data Model
created: 2026-06-11
updated: 2026-06-11
type: concept
tags: [game-data-analysis, materials]
sources: [raw/analysis/materials/00_summary.md]
confidence: high
---

# Materials Data Model

## Source
`documents/game_data/materials.json` — SHA256 in manifest. Unity runtime_reflection dump.

## Structure
- Material definitions used by shapes (quadrant `MetaShapeMaterial`)
- Each material maps to a letter code in shape hash encoding: C=Circle, R=Rectangle, S=Spike, W=Diamond, c=Crystal, P=Pin, -=Empty

## Key Mapping
| Code | Material | Description |
|------|----------|-------------|
| C | circle | Circle shape part |
| R | rectangle | Rectangle shape part |
| S | spike | Spike shape part  |
| W | diamond | Diamond shape part |
| c | crystal | Crystal material (special) |
| P | pin | Pin marker (factory I/O) |
| - | empty | Empty quadrant slot |

## Cross-References
- [[shape-data-model]]: quadrant Parts[].Shape references this enum
- [[fluid-data-model]]: shared Color palette for painting operations
- [[game-data-manifest]]: Unity runtime reflection dump surface
