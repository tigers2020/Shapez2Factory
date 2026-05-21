# Reconstructed Schema — `shapes.json`

**Align with** `documents/game_data_analysis/items/03_reconstructed_schema.md` — same tables, different JSON paths.

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `shape_recipe` | Recipe header | What shape codes exist? | `[*].definition_snapshot.*` | layers, items subset | Observed |
| `shape_recipe_layer` | Layer stack | Layer order / hash segment? | `Layers[]` | recipe | Observed |
| `shape_quadrant_slot` | Quadrant fill | Shape+color per slot? | `Parts[]` | kinds, fluid_color | Observed |
| `shape_component_kind` | Subpart lookup | Subpart kinds? | `Shape.name` | — | Observed |
| `game_data_import_batch` | Provenance | Which dump? | manifest | → all | Observed |
| `unknown_property` | Extensions | New keys? | any | audit | Planned |

---

## `shape_recipe` (path variant for shapes.json)

| Column | Source path (shapes.json) |
| ------ | ------------------------- |
| `operation_uid` | `definition_snapshot.UniqueOperationId` |
| `shape_hash` | `definition_snapshot.Hash` |
| `quadrant_count` | `definition_snapshot.PartCount` |
| `layer_count` | `len(Layers)` |
| `dump_stable_id` | `[*].stable_id` (unique in shapes file) |
| `catalog_source` | constant `full` | inferred | vs `items` subset |

**Unique:** `operation_uid`, `shape_hash`.

**Domain question:** “What is the complete shape recipe catalog for planner and research costs?”

---

## Child tables

Same as items: `shape_recipe_layer`, `shape_quadrant_slot` — paths use `definition_snapshot.Layers` (no `.Definition.` segment).

---

## Import strategy vs `items.json`

| Option | Recommendation |
| ------ | -------------- |
| Import shapes only | **Yes** — superset (1170 recipes) |
| Import items separately | Skip duplicate hashes or mark `catalog_source=items_subset` |
| Merge | Upsert on `shape_hash`; 70 item rows overwrite nothing if identical |

---

## Anti-patterns

| Rejected | Why |
| -------- | --- |
| `shapes_raw_json` | Forbidden |
| 1170 `ShapeDefinition` tables | C# mirror |
| JSONField `Layers` | Normalize |
| PK = `display_name_key` `#N` | Dump label |
