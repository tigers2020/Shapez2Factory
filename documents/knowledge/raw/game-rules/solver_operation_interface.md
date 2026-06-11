# Solver Operation Interface and Code Mapping

## Domain Protocol (`shapez_core`)

[`django_apps/shapez_core/domain/operation.py`](../../django_apps/shapez_core/domain/operation.py):

```python
class Operation(Protocol):
    name: str
    input_count: int
    output_count: int

    def apply(self, inputs: tuple[Shape, ...]) -> tuple[Shape, ...]:
        ...
```

`Shape` type: [solver_domain_model.md](solver_domain_model.md).

## Execution Engine (`shapez_solver`)

Entry point from recipes/macros: [`OperationEngine.apply`](../../django_apps/shapez_solver/services/operation_engine.py) (`OperationType` + `Recipe.color`, etc.). UI meta (label, icon, I/O counts): `OPERATION_CATALOG` in [`operation_catalog.py`](../../django_apps/shapez_solver/domain/operation_catalog.py).

## `OperationType` ↔ Behavior (Summary)

| `OperationType` | I/O (definition) | Implementation / Notes |
| --- | --- | --- |
| `cutter` | 1 → 2 | `cut_vertical_halves` → `(west, east)` ([shape_encoding.md](shape_encoding.md)) |
| `half_destroyer` | 1 → 1 | keep west only |
| `splitter` | 1 → 2 | duplicate same shape |
| `swapper` | 2 → 2 | single layer only: `swap_half_planes_single_layer` (east half NE+SE exchange) |
| `rotate_cw` / `rotate_ccw` / `rotate_180` | 1 → 1 | [`shape_operations`](../../django_apps/shapez_core/domain/shape_operations.py) |
| `stacker` | 2 → 1 | bottom+top, stack on merge failure + gravity and cap ([`operation_engine`](../../django_apps/shapez_solver/services/operation_engine.py)) |
| `painter` | 1 → 1 | `color` argument required |
| `color_mixer` | 2 → 1 | `color_mix_semantics` |
| `pin_pusher` | 1 → 1 | pin layer + post-processing |
| `crystal_generator` | 2 → 1 (catalog) | [`crystal_fill`](../../django_apps/shapez_core/domain/crystal_geometry.py); engine uses first shape only. Color: `crystal_color` in `apply_operation`, graph node `crystal_color`, or **uniform color from second input shape** — [crystal_mechanics.md](crystal_mechanics.md) |

## Pure Transform vs Solver Policy

- **Pure (coordinates only)**: rotate, vertical half, east-half swap, same-layer non-contiguous merge → [`shape_operations.py`](../../django_apps/shapez_core/domain/shape_operations.py).
- **Crystal**: generation, cluster, shatter → [`crystal_geometry.py`](../../django_apps/shapez_core/domain/crystal_geometry.py).
- **Policy/approximation**: post-stack gravity, max 4 layers, Painter, Color mixer, Pin → [`operation_engine.py`](../../django_apps/shapez_solver/services/operation_engine.py).

## Principles

- Keep I/O, DB, HTTP outside the domain ([architecture.mdc](../../.cursor/rules/architecture.mdc)).
