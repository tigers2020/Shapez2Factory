# Solver Internal Representation (`shapez_core` Canonical)

Below are the types actually used in this repo from [`django_apps/shapez_core/domain/shape.py`](../../django_apps/shapez_core/domain/shape.py).

## ShapePart

| Field | Meaning |
| --- | --- |
| `kind` | One-char shape code: `C` circle, `R` rectangle, `S` spike, `W` rhombus, `c` crystal, `P` pin, `-` empty |
| `color` | One-char color code (`u`,`r`,`g`, … or `-` for empty) |
| `material` | Implementation meta: e.g. `solid`, `empty`, `pin`, `crystal` |

Empty quadrants use **`EMPTY_PART`** (`kind=="-"`, `color=="-"`), not `None`.

Parser and catalog mapping: [`shape_catalog.py`](../../django_apps/shapez_core/domain/shape_catalog.py).

## ShapeLayer

- `quadrants`: length-4 tuple, order **SW, NW, NE, SE** ([shape_encoding.md](shape_encoding.md)).

## Shape

- `layers`: tuple of `ShapeLayer` from bottom to top. At least 1 layer.
- `canonical_code`: four tokens per layer concatenated, layers separated by `:`.

Crystal (`kind`=`c`) has different generation/destruction rules than normal shapes — [crystal_mechanics.md](crystal_mechanics.md), [`crystal_geometry.py`](../../django_apps/shapez_core/domain/crystal_geometry.py).

## Related

- [shape_encoding.md](shape_encoding.md)
- [core_abstraction.md](core_abstraction.md)
