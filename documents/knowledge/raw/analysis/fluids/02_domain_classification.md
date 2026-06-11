# Domain Classification — `fluids.json`

## Envelope fields

| JSON field | Classification | Notes |
| ---------- | -------------- | ----- |
| `definition_snapshot.Color.name` | **domain entity** key | Canonical palette name |
| `definition_snapshot.Color` (object) | **entity attribute** | Color payload |
| `definition_snapshot.$type` | **runtime / reflection / debug metadata** | Maps to `fluid_kind=color_fluid` enum |
| `stable_id` | **source metadata** (non-unique) | **Not** a domain PK in this dump |
| `source_guid` | **source metadata** | Constant `ColorFluid` |
| `display_name_key` | **source metadata** | Constant; not per-color |
| `source_path` | **source metadata** | Empty |
| `source_type_name` | **source metadata** | `ColorFluid` — not ORM model name |

## Inferred domain attributes

| Concept | Classification | Source |
| ------- | -------------- | ------ |
| `fluid_kind` | **enum / choice** | constant `ColorFluid` → `color_paint` |
| `solver_color_code` | **entity attribute** (inferred) | map from `COLOR_KINDS` in `shape_catalog.py` (`r`,`g`,`b`,…) |
| `is_primary_source_color` | **entity attribute** (inferred) | `FLUID_SOURCE_PRIMARY_COLORS` in domain code |
| `source_row_index` | **ordered child record** | array index 0–8 |
| `unity_instance_id` | **runtime / reflection / debug metadata** | `instance_id` |

## `Color.name` values → domain enums

| `Color.name` | Inferred `solver_color_code` | Inferred primary? |
| ------------ | ---------------------------- | ----------------- |
| Red | `r` | yes |
| Green | `g` | yes |
| Blue | `b` | yes |
| Cyan | `c` | derived |
| Magenta | `m` | derived |
| Yellow | `y` | derived |
| White | `w` | derived |
| Black | — | **needs human review** (not in `COLOR_KINDS`; used in items) |
| Uncolored | `u` | special |

**Human review:** Reconcile `Black` vs catalog `COLOR_KINDS["-"]` (Empty).

## Special rule compliance

- `ColorFluid` / `MetaShapeColor` → runtime/source metadata labels, not Django models.
- No `Game.Content.*` strings present.

## Unknown / needs human review

| Item | Question |
| ---- | -------- |
| Why nine rows share one `stable_id` | Exporter dedup bug or intentional singleton type expansion? |
| `Black` vs empty color `-` | Same fluid or distinct? |
| Relation to pipe fluids | This file is **paint/shape color**, not `FluidPort*` buildings |
| Link to `items.json` layers | FK by color name vs instance_id? |
