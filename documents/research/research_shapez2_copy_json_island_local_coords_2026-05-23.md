# Shapez2 copy JSON — island blueprint local coordinates



**Status**: Contract fixed (game paste verified, 2026-05-23)  

**Code**: `django_apps/asteroid_lab/snapshots/copy_json_coords.py`



## Summary



`X` / `Y` / `R` in decoded `BP.Entries` from a `SHAPEZ2-4-…` copy string are **not asteroid world absolute coordinates** but **local grid coordinates inside the pasted Island blueprint**.



| Rule | Meaning |

|------|------|

| Omitted `X` / `Y` / `R` | `0` |

| `X + 1` | One cell **to the right** on screen |

| `Y + 1` | One cell **down** on screen |

| `X == 0` | **Valid** in copy JSON (e.g. center extension) |



**Do not confuse**: copy **island-local**, reconstruction **world map** (no `x == 0` column), gene **canonical E** — separate frames. **PR-F:** dense server `(server_x, server_y)` **removed** — archived: [`research_asteroid_server_coords_layout_fingerprint_2026-05-16.md`](research_asteroid_server_coords_layout_fingerprint_2026-05-16.md).



## Verification Example (3-ext + miner + belt)



**Copy code** (copied from game):



```text

SHAPEZ2-4-H4sIAJmKEWoA/5SQwQrCMBBE/2XwGA+1ByFHsUJBQaqIIiJLGzEQ05KkaCn5d9PmInqShYVl38zA9DiAJ0k6Z1hswXtMXNcIcORWka7AkJe1Hh5LcgR+hgw33ypyt9o8LJhulYoL9k6N4EUbBxfPkGlnpLBB2OMIPp0xnEIgwz5krKmrW3fdDbKN1MJkLye0lSHQs8gnf/D/GAewAE8jvmuoFAuh3HVVmyeZ6oM6fbE/1vCX0J3UZLqDMGPGWKj3bwEGAPvbCnpcAQAA$

```



Decoded `Entries` (some keys omitted):



```json

[

  {"X": -2, "Y": 1, "T": "Layout_ShapeMinerExtension"},

  {"X": -1, "Y": 1, "T": "Layout_ShapeMinerExtension"},

  {"Y": 1, "T": "Layout_ShapeMinerExtension"},

  {"X": 1, "R": 3, "T": "SpaceBelt_Forward"},

  {"X": 1, "Y": 1, "R": 3, "T": "Layout_ShapeMiner"}

]

```



Coordinates after applying omitted fields:



| Screen (Y=0 top, Y=1 bottom) | `(X, Y)` | Type |

|-------------------------|----------|------|

| Left ext ×3 (row 1) | `(-2,1)`, `(-1,1)`, `(0,1)` | `Layout_ShapeMinerExtension` |

| Right miner (row 1) | `(1,1)` | `Layout_ShapeMiner` |

| Belt above miner (row 0) | `(1,0)` | `SpaceBelt_Forward` (`Y` omitted → `0`) |



ASCII (copy local, `Y` increases downward):



```text

Y=0:              (1,0) belt

Y=1:  (-2,1) (-1,1) (0,1) (1,1) miner

```



Near local origin: `(0,1)` = third extension, `(1,1)` = miner, `(1,0)` = belt above miner.



## Coordinate Frame Comparison



| Frame | `X==0` | Use |

|--------|--------|------|

| **Copy JSON island-local** | Allowed | Game paste / export `BP.Entries` |

| **Island map grid (`Coord`)** | Same as copy-local at lab boundary | fingerprint, optimization input (PR-F) |

| **World / reconstruction map** | **No column** | transport BFS, asteroid evidence |



Details (world map): [`research_blueprint_grid_coordinates_2026-05-10.md`](research_blueprint_grid_coordinates_2026-05-10.md).



## Implementation Map



| Stage | Module |

|------|------|

| Decode (document omitted → 0) | `decode_adapter`, `shapez_copy_decode` |

| Read island-local | `copy_json_coords` |

| Attach island meta | `attach_island_coord_meta_to_decoded_json` / `island_bbox.py` |

| Lab → game export XY | `blueprint_canonical_export.translate_lab_entries_to_official_xy` |



## Tests



- `tests/unit/asteroid_lab/test_copy_json_island_local_coords.py` — omitted keys·verification copy string

- `tests/unit/asteroid_lab/test_island_bbox.py` — island bbox / persist meta

