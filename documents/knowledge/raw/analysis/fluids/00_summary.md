# File Inventory — `fluids.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/fluids.json` |
| File name | `fluids.json` |
| Manifest hash | `sha256:8a9b9b776f6ea2d2a19cdadb8159958fc916322ba6e25b91d2082b476a7ba975` |
| Approx. size | **2,749 bytes** |
| Dump context | `manifest.json` → `source_method: runtime_reflection` |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **9** |
| Element type | **object** (homogeneous envelope) |
| Nesting depth | **2** (envelope + small `definition_snapshot`) |

## Critical inventory finding

The dump repeats the **same envelope** nine times; only `definition_snapshot.Color.name` (and matching `instance_id`) differs:

| Field | Distinct values |
| ----- | --------------- |
| `stable_id` | **1** (identical on all 9 rows) |
| `source_guid` | **1** (`ColorFluid`) |
| `display_name_key` | **1** (`ColorFluid`) |
| `source_type_name` | **1** (`ColorFluid`) |
| `definition_snapshot.Color.name` | **9** (palette colors) |

**Implication:** This file is a **color-fluid palette expansion**, not nine independent fluid entities with unique hash IDs.

## Major object groups

| Logical group | Count | Discriminator |
| ------------- | ----- | ------------- |
| Color-fluid palette entries | **9** | `Color.name` |
| Fluid type (serializer) | **1** | `$type: ColorFluid` |

### Palette colors (full list)

`Red`, `Green`, `Blue`, `Cyan`, `Magenta`, `Yellow`, `White`, `Black`, `Uncolored`

## Envelope fields (9/9 identical except snapshot color)

| Field | Type | Notes |
| ----- | ---- | ----- |
| `stable_id` | 64-char hex | **Not unique** — dump reuse |
| `source_guid` | string | `ColorFluid` |
| `source_path` | string | `""` |
| `source_type_name` | string | `ColorFluid` (dump label) |
| `display_name_key` | string | `ColorFluid` |
| `definition_snapshot` | object | `Color` + `$type` |

## Repeated structures

| Structure | Notes |
| --------- | ----- |
| Envelope (6 keys) | Identical across rows |
| `definition_snapshot.Color` | `$unity`, `name`, `instance_id` |
| `definition_snapshot.$type` | Always `ColorFluid` |

## Arrays

- Root array only (9 elements).
- No nested arrays inside records.

## Nested objects

- `definition_snapshot` (flat: `Color` object + `$type` string).

## Candidate IDs

| Field | Usable as PK? | Recommended role |
| ----- | ------------- | ---------------- |
| `stable_id` | **No** (1 value) | Import audit / non-unique warning |
| `Color.name` | **Yes** (9 unique) | **Canonical business key** (`color_name`) |
| `instance_id` | **No** | Unity runtime ref (audit only) |
| `source_row_index` | **Yes** | Deterministic ordering (0–8) |

## Runtime / reflection / debug strings

| Pattern | Classification |
| ------- | -------------- |
| `source_type_name: ColorFluid` | source metadata |
| `$type: ColorFluid` | runtime / serializer metadata → `fluid_kind` enum |
| `$unity: MetaShapeColor` | source metadata (engine type label) |
| `instance_id` | runtime / reflection / debug metadata |

No `Game.Content.*` assembly strings in this file.

## Cross-file references

| File | Relationship |
| ---- | ------------ |
| `items.json` | Uses `MetaShapeColor` with same color names / `instance_id` values (e.g. Black `20056`) |
| `shapes.json` | All 9 color name strings appear in file text |
| `shape_catalog.py` (`COLOR_KINDS`) | Maps single-letter codes (`r`,`g`,`b`,…) to same display names |
| `buildings.json` | 2/9 color name text hits (incidental) |
| Pipe/fluid transport | **`belts_pipes_transport.json`** — different domain (pipe networks), not this palette |

## Design implication

Normalize to **`fluid_color`** (9 rows) under one **`fluid_kind = color_paint`** (or similar domain name), keyed by `color_name`. Do **not** create nine rows keyed by duplicate `stable_id`. Do **not** use `ColorFluid` as a Django model name.
