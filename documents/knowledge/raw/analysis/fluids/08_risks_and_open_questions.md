# Risks and Open Questions — `fluids.json`

## Uncertain meaning

| Item | Risk |
| ---- | ---- |
| Duplicate `stable_id` on all rows | Exporter lists one type, many colors — **must not** use as PK |
| `Black` vs catalog empty `-` | Two “non-primary” concepts may collide |
| File name `fluids.json` vs content | Palette only — pipe fluids live elsewhere |
| `Uncolored` vs unpainted empty | Gameplay distinction |

## Human review

| Question |
| -------- |
| Should domain table be `fluid_color` or `shape_paint_color`? |
| Import `solver_color_code` from JSON or hard-code via `COLOR_KINDS`? |
| Is `instance_id` stable across dumps for regression tests? |

## Runtime metadata risks

- Model named `ColorFluid` or `MetaShapeColor`
- Using `instance_id` as FK from items import

## Ambiguous IDs

- One `stable_id`, nine colors — **canonical key = `color_name` only**

## Dynamic schema

- Future dumps may add new colors or fluid types (`ChemFluid`, etc.)
- Count guard + enum extension

## Version drift

- Manifest hash on 9 rows + color set
- `instance_id` values may change per Unity session

## Missing cross-reference targets

- No FK from pipe/fluid buildings
- `translations.json` incomplete (manifest)
- Black solver letter code absent in `COLOR_KINDS`

## Defer

- `fluids_raw` table
- Per-color simulation chemistry tables (not in dump)

## Risk summary

| Area | Level |
| ---- | ----- |
| Schema size | **Low** (flat) |
| ID semantics | **High** (duplicate stable_id) |
| Domain naming | **Medium** (paint vs pipe fluid) |
| Catalog alignment | **Medium** (Black, Uncolored) |
