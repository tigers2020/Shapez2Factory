# Operation: Rotater (Rotation)

## Role

Rearranges the shape's **4-quadrant layout** under rotation. In the solver this is usually a **simple permutation**.

## This Project's Quadrant Order

One layer's `quadrants` indices are **[SW, NW, NE, SE]** (= `[0]` … `[3]`). May differ from official viewer string order → [shape_encoding.md](shape_encoding.md).

Implementation canonical: `rotate_cw` / `rotate_ccw` / `rotate_180` in [`django_apps/shapez_core/domain/shape_operations.py`](../../django_apps/shapez_core/domain/shape_operations.py) and unit tests.

## Permutation (reindex 0~3)

Which old index feeds `new[i]`:

| Operation | `new[0]` (SW) | `new[1]` (NW) | `new[2]` (NE) | `new[3]` (SE) |
| --- | --- | --- | --- | --- |
| CW | old[3] | old[0] | old[1] | old[2] |
| CCW | old[1] | old[2] | old[3] | old[0] |
| 180° | old[2] | old[3] | old[0] | old[1] |

## Example (Conceptual)

String examples in documents using other coordinate orders may **not match byte-for-byte**. Verify rotation with project shape codes (e.g. `RuSuCuWu` → CW gives `WuRuSuCu`).

## Notes

- Multi-layer shapes: apply the **same permutation to every layer**.
- Rotation and cut order are central to production-line optimization ([operation_cutter.md](operation_cutter.md)).
