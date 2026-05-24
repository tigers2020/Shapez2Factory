# Shape Code Structure (Project Canonical)

## Difference from Official Viewer (Reference)

Official shape viewers often describe layer strings as two-character tokens listed **clockwise from top-right** (NE → SE → SW → NW).

**The shapez2Solver repo canonical implementation differs.** Parser, `Shape.canonical_code`, and quadrant order in [`django_apps/shapez_core/domain/shape_pattern.py`](../../django_apps/shapez_core/domain/shape_pattern.py) follow the **project table** below. Pasting strings into official tools may not produce the same visual.

## This Project: One Layer (8 Characters) Token Order

One layer consists of four **two-character tokens** (shape 1 char + color 1 char). **Token index and compass/internal array index**:

| Token index (0~3) | `ShapeLayer.quadrants[i]` | `QuadrantPosition` |
| --- | --- | --- |
| 0 | `quadrants[0]` | SW |
| 1 | `quadrants[1]` | NW |
| 2 | `quadrants[2]` | NE |
| 3 | `quadrants[3]` | SE |

So the layer string runs **SW → NW → NE → SE**.

## Example String

```text
RuCw--Cw:----Ru--
```

## Interpretation Example (This Project Coordinate System)

```text
Layer 0 (bottom): SW=Ru, NW=Cw, NE=--, SE=Cw  →  RuCw--Cw
Layer 1 (top):    SW=--, NW=--, NE=Ru, SE=--  →  ----Ru--
```

## Rules Summary

| Element | Meaning |
| --- | --- |
| `:` | Layer separator |
| Layer order | **Bottom layer → top layer** |
| One layer | **4 quadrants**, each a **2-character token** |
| Token order | **SW, NW, NE, SE** (same as `shape_pattern.quadrant_at_index`) |
| `Ru`, etc. | Shape type char + color char |
| `--` | Empty quadrant |

## Solver Implementation Notes

- Single axis for string ↔ `Shape` conversion: [`django_apps/shapez_core/services/shape_code_parser.py`](../../django_apps/shapez_core/services/shape_code_parser.py), [`shape_codec.py`](../../django_apps/shapez_core/services/shape_codec.py).
- Rotation and cut permutation definitions: [operation_rotater.md](operation_rotater.md), [`shape_operations` module](../../django_apps/shapez_core/domain/shape_operations.py), and tests are canonical.
