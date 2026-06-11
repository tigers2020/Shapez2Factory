# File Inventory — `materials.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/materials.json` |
| File name | `materials.json` |
| File size | **1,025 bytes** |
| Manifest hash | `sha256:bf78de78188ea87675e16da6b009657a61cad7de549744e7fd489e7165e2d6cf` |
| Dump context | `manifest.json` → `source_method: runtime_reflection`, v2 export |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **4** |
| Element shape | **Flat object** (no `definition_snapshot` wrapper) |

## Per-element keys (4/4 identical schema)

| Key | Type | Distinct values |
| --- | ---- | ----------------- |
| `stable_id` | 64-char hex | **4** (unique per row) |
| `source_type_name` | string | **1** (`UnityEngine.Object`) |
| `source_guid` | string | **1** (empty `""`) |
| `source_path` | string | **4** (logical asset path) |
| `display_name_key` | string | **4** (matches path basename) |
| `material_path` | string | **4** (same as `source_path` / `display_name_key`) |

## Major object groups

| Group | Count | Notes |
| ----- | ----- | ----- |
| Material content records | 4 | Full population sampled for analysis |
| Nested `definition_snapshot` | 0 | Unlike `items.json` / `buildings.json` |

## Repeated structures

Homogeneous envelope on every row; no arrays or nested objects inside elements.

## Arrays detected

- Root array only (length 4)

## Candidate IDs

| Field | Role |
| ----- | ---- |
| `stable_id` | **Canonical content ID** — unique; FK target from `asset_references.json` (`ref_stable_id`) |
| `material_path` | **Canonical logical name** — UNIQUE business key |
| `source_path` | Same string as `material_path` in this dump |
| `display_name_key` | i18n lookup key (no `translations.json` rows yet) |
| `source_guid` | Empty — not usable |
| `source_type_name` | Dump channel label only |

## Runtime / reflection / debug strings

| Value | Classification |
| ----- | -------------- |
| `UnityEngine.Object` | source metadata (`source_type_name`) |
| Empty `source_guid` | source metadata |

**Not** domain model names (`UnityEngineObject`, etc.).

## Source metadata

- No shader name, render queue, texture slots, or color properties in dump — **path identity only**.
- Export captures material asset registry entries, not full Material property bags.

## Cross-file references

| File | Relationship |
| ---- | ------------ |
| `asset_references.json` | **4** rows `asset_type: material` with `ref_stable_id` → each `stable_id` (1:1) |
| `manifest.json` | `file_hashes.materials.json` integrity gate |
| `prefabs.json` / `sprites.json` | Sibling content registries (same envelope pattern) |

## Material paths (full file)

| `material_path` | Role (inferred) |
| --------------- | ----------------- |
| `LabelTextMaterial` | UI label rendering |
| `MixerFluidMaterial` | Fluid mixer visualization |
| `PainterRollMaterial` | Painter building roll (full) |
| `PainterRollMinimalMaterial` | Painter roll (minimal variant) |

## Design implication

Four rows → four **`material_asset`** records keyed by **`stable_id`** and **`material_path`**. No `materials_raw_json`, no `UnityEngine.Object` table, no JSONField for the array.
