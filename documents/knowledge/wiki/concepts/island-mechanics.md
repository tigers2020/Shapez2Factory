---
title: Island Mechanics (Coordinate Frames)
created: 2026-06-12
updated: 2026-06-12
type: concept
tags: [asteroid-lab, game-rules]
sources:
  - documents/knowledge/raw/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md
confidence: high
---

# Island Mechanics

> **Canon for copy JSON:** `django_apps/asteroid_lab/snapshots/copy_json_coords.py` + research doc below. Wiki is retrieval summary.

## Core rule (source)

`X` / `Y` / `R` in decoded `BP.Entries` from a `SHAPEZ2-4-…` paste are **island-local blueprint grid** coordinates — **not** asteroid world absolute coords.

| Rule | Meaning |
|------|---------|
| Omitted `X` / `Y` / `R` | Default **0** |
| `X + 1` | One cell right on screen |
| `Y + 1` | One cell down on screen |
| `X == 0` | **Valid** in copy JSON (e.g. center extension) |

## Three frames — do not mix (source)

| Frame | `X == 0` | Use |
|-------|----------|-----|
| **Copy JSON island-local** | Allowed | Game paste / export `BP.Entries` |
| **Island map grid (`Coord`)** | Same as copy-local at lab boundary | Fingerprint, optimization input |
| **World / reconstruction map** | **No column** | Transport BFS, asteroid evidence |

Gene canonical **E** and server dense coords are **separate** frames (see raw research cross-links).

## Code map (source)

| Stage | Module |
|-------|--------|
| Decode omitted → 0 | `decode_adapter`, `shapez_copy_decode` |
| Read island-local | `copy_json_coords` |
| Island meta / bbox | `island_bbox.py`, `attach_island_coord_meta_to_decoded_json` |
| Lab → game export XY | `blueprint_canonical_export.translate_lab_entries_to_official_xy` |

## Tests (source)

- `tests/unit/asteroid_lab/test_copy_json_island_local_coords.py`
- `tests/unit/asteroid_lab/test_island_bbox.py`

## Cross-References

- [[asteroid-lab-algorithm]]: reconstruction uses world map, not copy-local
- [[transport-system]]: belt/pipe layout IDs in copy entries
- [[game-data-manifest]]: paste decode contract stability
