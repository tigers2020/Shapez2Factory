# Final Canonical Schema Recommendation

Unified domain model for `game_data` imports.  
**Source report structure ≠ final DB structure.**

Status: **Approved** | **Needs review** | **Rejected**

---

## Layer 0 — Import & integrity

> **Django mapping:** [`10_import_metadata_unification.md`](10_import_metadata_unification.md) — `ImportBatch`, `ArtifactChecksum`, `SourceObject`, `UnknownProperty` (no parallel `GameData*` tables).

### `game_data_import_batch` — **Approved** (`ImportBatch`)

| Column | Constraints |
| ------ | ----------- |
| `id` | PK |
| `manifest_self_hash` | UNIQUE |
| `game_version`, `unity_version`, `dump_mod_version`, `dump_schema_version` | |
| `dump_timestamp_utc`, `source_method` | |
| `imported_at` | inferred |

**Origins:** all reports, manifest.

### `game_data_artifact_checksum` — **Approved** (`ArtifactChecksum`)

UK: `(import_batch_id, artifact_filename)`. Columns: `expected_sha256`, `import_status`, `is_incomplete`.

**Origins:** manifest.

### `export_warning`, `export_incomplete_section` — **Approved**

**Origins:** manifest.

### `localization_export_status` — **Approved** (Needs review link to incomplete)

**Origins:** translations, manifest.

### `source_object_record`, `unknown_property` — **Approved** (`SourceObject`, `UnknownProperty`)

**Origins:** all planned.

---

## Layer 1 — Content assets (merged)

### `game_content_asset` — **Approved** (replaces prefab/sprite/material tables)

| Column | Notes |
| ------ | ----- |
| `stable_id` | UNIQUE |
| `content_kind` | enum prefab \| sprite \| material |
| `content_path` | was prefab_path / sprite_path / material_path |
| `display_name_key`, `dump_source_type`, `unity_source_guid` | |
| `import_batch_id`, `source_row_index` | |

**Origins:** prefabs, sprites, materials, asset_references.

### `asset_meta_reference` — **Approved**

FK: `content_stable_id` + `content_kind` → `game_content_asset`. UK: `meta_stable_id`, `logical_path`.

**Origins:** asset_references.

---

## Layer 2 — Buildings

### `building_group` — **Approved** (unifies `building` + `building_group` reports)

| Column | Notes |
| ------ | ----- |
| `group_key` | UK (business) |
| `stable_id` | audit per source file |
| `display_profile` | plain \| lazy_overlay |
| flags: transport, placement_mode, player_buildable, … | |

### `building_localization_overlay` — **Approved**

FK → `building_group`. LazyText keys.

### `building_simulation_setting` — **Approved**

1:1 `building_group`. Merged from buildings + building_groups simulation_parameters.

### `building_group_member` — **Approved**

FK `building_group_id`, FK `building_variant_id`, `ordinal`, `member_resolution`.

### `building_variant` — **Approved** (canonical owner: building_variants.json)

| Column | UK |
| ------ | -- |
| `internal_name` | business |
| `stable_id` | dump |

Children: **`building_connector`**, **`building_footprint_tile`**.

**Origins:** building_variants (primary), belts_pipes_transport (duplicate snapshot import optional).

### `transport_building_registry` — **Approved**

UK `transport_kind`. Links to variant by internal_name / snapshot hash — **Needs review** FK.

### `building_placement_rule` — **Approved**

FK → `building_group`.

---

## Layer 3 — Shapes & fluids

### `fluid_color`, `fluid_kind` — **Approved**

**Origins:** fluids.

### `shape_component_kind` — **Approved**

**Origins:** items, shapes.

### `shape_recipe`, `shape_recipe_layer`, `shape_quadrant_slot` — **Approved**

Canonical keys: `shape_hash`, `operation_uid`. Import shapes.json first; upsert items subset.

**Origins:** shapes, items, research_unlocks (costs).

---

## Layer 4 — Research

### `research_upgrade`, `research_mechanic` — **Approved**

### `research_milestone`, `research_side_quest`, `research_side_upgrade` — **Approved**

Shared children: **`research_unlock_cost`** (→ shape_recipe), **`research_unlock_reward`**, **`research_prerequisite`**.

### `research_global_config` — **Approved**

**Origins:** research_unlocks. Layout index table — **Needs review** (`progression_layout_index`).

---

## Layer 5 — Simulation & UI

### `simulation_system` (C-lite) — **Approved**

`simulation_profile` FK, `simulation_type`, `simulation_state_type`, `simulation_clr_provenance` (CLR only; renamed from `ImportAudit`), `connectable_simulation` + connector/lane/bounds children, `global_belt_speed_policy`, `simulation_runtime_audit` (JSON audit only). UK upsert: `(import_batch, source_stable_id)`. `canonical_id` grouped, non-unique.

**Removed:** `simulation_system_entry`, `simulation_factory_stub`, domain `clr_type_audit`.

### `toolbar_element` + extensions — **Approved**

`toolbar_tree_edge`, `toolbar_building_placement`, `toolbar_island_placement`, kinds for group/separator/category.

---

## Layer 6 — Reflection & l10n

### `clr_type_registry_entry` — **Approved**

### `localized_message` — **Approved** (0 rows until re-export)

---

## Rejected

| Proposed | Reason |
| -------- | ------ |
| `*_raw_json` tables | Forbidden all reports |
| Per-`$type` tables | Serializer mirror |
| `ResearchUnlockManager` entity | Singleton dump type |
| `BuildingDefinition` table | Nested extract → variant scalars |
| `UnityEngineObject` entity | Runtime label |

---

## Import order (canonical)

```text
1. manifest → game_data_import_batch + artifact_checksums
2. fluids → fluid_color
3. shapes → shape_recipe tree
4. building_variants → building_variant + connectors + tiles
5. building_groups + buildings → unified building_group + members + l10n
6. game_content_asset (prefabs, sprites, materials)
7. asset_meta_reference
8. research_unlocks
9. simulation_systems
10. toolbar_entries
11. translations → localization_export_status only
12. raw_type_index (optional validation)
```

---

## Cross-report ownership matrix

| JSON file | Owns canonical tables |
| --------- | --------------------- |
| manifest | import batch, checksums, warnings |
| building_variants | building_variant, connector, tile |
| building_groups + buildings | building_group (merge) |
| shapes | shape_recipe* |
| fluids | fluid_color |
| prefabs/sprites/materials | game_content_asset |
| asset_references | asset_meta_reference |
| research_unlocks | research_* |
| simulation_systems | simulation_system* (C-lite) |
| toolbar_entries | toolbar_* |
| translations | localization_export_status |
| raw_type_index | clr_type_registry_entry |
| items | subset upsert into shape_recipe* |
| belts_pipes_transport | transport_building_registry + checksum only (no second variant import) |
