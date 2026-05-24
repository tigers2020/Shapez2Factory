# Fluid Carrier

## Concept

In the game, an **empty fluid carrier** is not a shape product but carries **one uniform color (ink) code** through pipes. This repo models that contract as a **`Shape` code with the same color character on all paintable quadrants** (pure fluid). Extraction rules: `pure_fluid_color` in `django_apps/shapez_solver/services/fluid_semantics.py`.

## Selectable Colors at Source

- Fluid **sources** (`source_carrier: "fluid"` on `graph_document` nodes) allow only **primary RGB** characters: `r`, `g`, `b`.
- **Achromatic `u`** and **secondary colors `c`, `m`, `y`, `w`** cannot be chosen directly at fluid sources. (Legacy graphs omitting `source_carrier` behave as before.)

## Secondary Colors and Y/M/C/W

- `c` (cyan), `m` (magenta), `y` (yellow), `w` (white), etc. are produced **only via `color_mixer`**.
- Mix table implementation: `django_apps/shapez_solver/services/color_mix_semantics.py`. Extend that module after separate research if more mixes (e.g. white combinations) are needed.

## CMYK and `k` (Black)

- When mapping community YMCKW terminology, this project's **single-character color codes** include `c`, `m`, `y`, `w` but **no dedicated `k` (black) character yet** (`COLOR_KINDS` in `django_apps/shapez_core/domain/shape_catalog.py`). Adding black to the model requires updating catalog, mix rules, and UI together.

## Painter Legacy `paint_color`

- The **single input + `paint_color`** path (not two wires: fluid + shape) is treated as inline ink; **RGB (`r`,`g`,`b`) only**.

## Intermediate, Palette Integration, Port Rules

- **Palette**: empty sources default to one **shape (material)** type. For fluid, set **carrier = fluid** in node edit then configure RGB fluid.
- **`source_carrier`**: on `kind: "shape"` with `role` `source` or `intermediate`, denotes **wire type**. `"fluid"` = liquid carrier; omit key (or strip on normalize) = material. Do not set `source_carrier` on output nodes with `role: "target"`.
- **Input ports (backend `recipe_graph_input_carrier` / frontend `recipeConnection.ts` — keep both in sync when changing)**:
  - `painter` 2-wire: index 0 = **fluid**, 1 = **material**; with `paint_color`, single **material** input only.
  - `painter` + `paint_color` 1-wire: **material**.
  - `color_mixer` 2-wire: both **fluid**.
  - `swapper`, `stacker`, `crystal_generator` 2-wire: both **material**.
  - Other unary operations: **material**.
- **Operation output → intermediate**: `color_mixer` output lane allows **fluid** intermediate only (`source_carrier: "fluid"`); other operation outputs are **material** intermediate. Recompute (`recipe_graph_recompute`) aligns intermediate to output.
- **Delivery (intermediate → output)**: both material and fluid intermediates allowed (same `shape_code` copy model).
- **UI**: when changing carrier or `shape_code`, remove edges on that node that violate the rules above.

## Related Documents

- [operation_color_mixer.md](operation_color_mixer.md)
- [operation_painter.md](operation_painter.md)
