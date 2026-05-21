# Cross-Reference Analysis — `fluids.json`

## FK relationships

| From | To | Status |
| ---- | -- | ------ |
| `fluid_color.color_name` | `items.json` `MetaShapeColor.name` | **Logical FK** (name match; no stable_id) |
| `fluid_color.solver_color_code` | `shape_catalog.COLOR_KINDS` | **Inferred** mapping table in code |
| `fluid_color` | `belts_pipes_transport` / pipe buildings | **No direct link** (different fluid concept) |

## M2M

**None.** Palette is a flat enumeration.

## Ordered child relationships

```text
game_data_import_batch
  └─ has many → fluid_color (9, ordered by source_row_index)
```

## Inferred reference diagram

```text
fluid_kind (color_paint)
  └─ has many → fluid_color
        ├─ Red / Green / Blue (primary sources)
        ├─ Cyan / Magenta / Yellow / White (derived)
        ├─ Black (items use; catalog mapping TBD)
        └─ Uncolored (default unpainted)

ShapeItem (items.json)
  └─ layers reference → fluid_color (by Color.name)

ShapeDefinition (shapes.json)
  └─ may reference → fluid_color (by name, TBD path)

BuildingFluidPort (belts_pipes_transport)
  └─ (no FK to fluid_color — pipe simulation separate)
```

## Unresolved references

| Reference | Notes |
| --------- | ----- |
| Duplicate `stable_id` | Cannot FK other tables to variant hash |
| `Black` ↔ `COLOR_KINDS["-"]` | Naming mismatch |
| `translations.json` | No per-color i18n in this file |
| `research_unlocks.json` | No hits expected for palette |

## Source metadata

- `$unity` / `instance_id` — engine snapshot only
- `source_type_name: ColorFluid` — provenance

## Cardinality

| Metric | Value |
| ------ | ----- |
| Rows | 9 |
| Unique `color_name` | 9 |
| Unique `stable_id` | 1 |
| Unique `instance_id` | 9 |
