# ruff: noqa: E501
"""Generate documents/game_data_analysis/_audit/*.md cross-document audit."""
from __future__ import annotations

from pathlib import Path

AUDIT = Path(__file__).resolve().parents[1] / "documents" / "game_data_analysis" / "_audit"

FILES = {
    "01_global_entity_registry.md": r"""# Global Entity Registry

Cross-scan of **153** reports under `documents/game_data_analysis/**` (17 JSON stems × 9 files).

Normalization rule: names below are **canonical working names**; report-local aliases noted in *Origins*.

---

## Infrastructure & provenance

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `game_data_import_batch` | all 17 | Single export bundle identity | `manifest_self_hash` or `(dump_timestamp_utc, dump_schema_version, dump_mod_version)` | parent of all imports | **Approved** |
| `game_data_artifact_checksum` | manifest | Per-file SHA-256 gate | `(import_batch_id, artifact_filename)` | → batch | **Approved** |
| `export_warning` | manifest | Export caveats | `(import_batch_id, warning_index)` | → batch | **Approved** |
| `export_incomplete_section` | manifest, translations | Failed sections | `(import_batch_id, section_code)` | → batch | **Approved** |
| `localization_export_status` | translations | Empty/incomplete l10n | `import_batch_id` 1:1 | overlaps `export_incomplete_section` | **Needs review** |
| `source_object_record` | most (planned) | JSON row audit | `(import_batch_id, source_file, source_index)` | → batch | **Approved** |
| `unknown_property` | all (planned) | Unmapped JSON keys | `(parent_table, parent_id, property_key)` | audit | **Approved** |

---

## Asset content & meta bridge

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `prefab_asset` | prefabs, asset_references | Prefab content identity | `stable_id` / `prefab_path` | ← meta | **Approved** (merge candidate) |
| `sprite_asset` | sprites, asset_references | Icon/sprite content | `stable_id` / `sprite_path` | ← meta | **Approved** (merge candidate) |
| `material_asset` | materials, asset_references | Material content | `stable_id` / `material_path` | ← meta | **Approved** (merge candidate) |
| `asset_meta_reference` | asset_references | .meta → content bridge | `meta_stable_id` | → content by kind | **Approved** |

---

## Buildings & placement geometry

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `building` | buildings | Player-facing buildable **group** (plain display keys) | `group_key` (= `source_guid`) | → members, rules | **Approved** |
| `building_group` | building_groups | Same 67 families with LazyText overlay | `group_key` / `stable_id` | → members, l10n | **Needs review** (vs `building`) |
| `building_variant` | building_variants, buildings, building_groups, belts_pipes_transport | Internal variant geometry + connectors | `internal_name` (`Id.Name`) | connectors, tiles | **Approved** (canonical owner: **building_variants**) |
| `building_connector` | building_variants, building_groups, buildings, belts_pipes_transport | IO endpoints | `(building_variant_id, ordinal)` | → variant | **Approved** |
| `building_footprint_tile` | building_variants, belts_pipes_transport | Occupied tiles | `(building_variant_id, ordinal)` or coords | → variant | **Approved** |
| `building_group_member` | buildings, building_groups | Group → variant membership | `(parent_group_id, ordinal)` | → variant | **Approved** (unify parent FK) |
| `building_placement_rule` | buildings, building_groups | Placement constraints | `(building_id or building_group_id, ordinal)` | → group | **Needs review** |
| `building_simulation_setting` | buildings | Sim/UI flags per group | `building_id` 1:1 | → building | **Approved** |
| `building_group_simulation_setting` | building_groups | Same flags on group row | `building_group_id` 1:1 | → building_group | **Merge?** with `building_simulation_setting` |
| `building_localization_overlay` | building_groups, buildings | LazyText title/description | `group_key` | → building/group | **Approved** |
| `building_group_localization_ref` | building_groups | LazyText keys only | `building_group_id` | → group | **Merge?** into overlay |
| `transport_building_registry` | belts_pipes_transport | Transport-kind registry (9 kinds) | `transport_kind` | → variant snapshot | **Approved** (not duplicate of `building`) |

---

## Shapes & fluids

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `shape_recipe` | items, shapes, research_unlocks | Shape code / operation | `shape_hash`, `operation_uid` | layers, slots | **Approved** (single table; items⊂shapes) |
| `shape_recipe_layer` | items, shapes | Layer stack | `(shape_recipe_id, layer_index)` | → recipe | **Approved** |
| `shape_quadrant_slot` | items, shapes | Quadrant shape+color | `(layer_id, quadrant_index)` | → kinds, fluid | **Approved** |
| `shape_component_kind` | items, shapes | Subpart lookup | `component_key` | — | **Approved** |
| `fluid_color` | fluids, items, shapes | Paint/fluid palette | `color_name` | ← slots | **Approved** |
| `fluid_kind` | fluids | Serializer family enum | constant | — | **Approved** |

---

## Research progression

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `research_upgrade` | research_unlocks | Upgrade id registry | `upgrade_key` | prereqs, quests | **Approved** |
| `research_milestone` | research_unlocks | Main ladder node | `node_key` | costs, rewards | **Approved** |
| `research_side_quest` | research_unlocks | Side quest | `node_key` | costs, rewards | **Approved** |
| `research_side_upgrade` | research_unlocks | Side upgrade | `node_key` | prereqs | **Approved** |
| `research_mechanic` | research_unlocks | Mechanic gate | `mechanic_key` | prereqs | **Approved** |
| `research_unlock_cost` | research_unlocks | Shape payment | `(parent_id, sort_order)` | → shape_recipe | **Approved** |
| `research_unlock_reward` | research_unlocks | Reward line | `(parent_id, sort_order)` | — | **Approved** |
| `research_prerequisite` | research_unlocks | Upgrade/mechanic deps | `(parent_id, required_key)` | → upgrade/mechanic | **Approved** |
| `research_global_config` | research_unlocks | Global tunables | `import_batch_id` singleton | — | **Approved** |
| `progression_layout_index` | research_unlocks (inferred) | Manager layout index | TBD | → nodes | **Needs review** |

---

## Simulation & toolbar

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `simulation_system_entry` | simulation_systems | CLR sim registration | `stable_id` + `simulation_kind_key` | factory/audit children | **Approved** |
| `simulation_factory_stub` | simulation_systems | Factory-only shell | `simulation_system_entry_id` | → entry | **Approved** |
| `global_belt_speed_policy` | simulation_systems | Belt speed buff | `import_batch_id` | → research_upgrade | **Approved** |
| `connectable_simulation_attachment` | simulation_systems | Connectable graph slot | `(entry_id, attachment_index)` | building audit | **Needs review** |
| `simulation_runtime_audit` | simulation_systems | Heavy CLR capture | `simulation_system_entry_id` | audit JSON only | **Approved** |
| `toolbar_element` | toolbar_entries | Flattened toolbar node | `tree_path` (= display_name_key) | tree edges | **Approved** |
| `toolbar_tree_edge` | toolbar_entries | Parent/child | `(parent_id, child_id, child_index)` | → elements | **Approved** |
| `toolbar_building_placement` | toolbar_entries | Places building variant | `toolbar_element_id` | `building_definition_key` | **Approved** |
| `toolbar_island_placement` | toolbar_entries | Island placement | `toolbar_element_id` | `island_group_name` | **Approved** |
| `toolbar_group_node` | toolbar_entries | Folder/category | `toolbar_element_id` | mechanic_key? | **Approved** |
| `toolbar_separator` | toolbar_entries | Separator | `toolbar_element_id` | — | **Approved** |

---

## Reflection catalog

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `clr_type_registry_entry` | raw_type_index | CLR type catalog | `(type_name, assembly_name)` | optional manifest DLL | **Approved** |
| `localized_message` | translations (planned) | Resolved strings | `(message_key, locale_code)` | all LazyText | **Approved** (0 rows today) |

---

## Rejected as domain entities (registry note)

| Dump label | Keep as |
| ---------- | ------- |
| `ShapeItem`, `ShapeDefinition`, `BuildingDefinition` | metadata / nested extract only |
| `AtomicStateful*System`2[[…]]` | `clr_type_audit` / `simulation_system_entry.clr_type_audit` |
| `UnityEngine.Object` | `dump_source_type` column |
| `Game.Core.Research.ResearchUpgradeId` | row discriminator only |

---

## Entity count summary

| Category | Tables |
| -------- | ------ |
| Infrastructure | 7 |
| Assets | 4 (+ 3 merge candidates) |
| Buildings | 12 |
| Shapes/fluids | 6 |
| Research | 9 |
| Simulation/toolbar | 10 |
| Reflection/l10n | 2 |
| **Total distinct canonical** | **~50** (post-merge target **~42**) |
""",
    "02_duplicate_entities.md": r"""# Duplicate Entity Detection

Semantic comparison across reports. Similarity 0–100.

| Entity A | Entity B | Similarity | Merge recommendation | Reason |
| -------- | -------- | ---------: | -------------------- | ------ |
| `shape_recipe` (items) | `shape_recipe` (shapes) | **98** | **Merge** — single table; dual JSON path extractor | Same columns; shapes is superset (1170⊃70); items uses nested `Definition` wrapper |
| `shape_recipe_layer` | `shape_recipe_layer` (shapes/items) | **98** | Merge with above | Identical child model |
| `shape_quadrant_slot` | `shape_quadrant_slot` (shapes/items) | **98** | Merge with above | Same |
| `prefab_asset` | `sprite_asset` | **88** | **Merge** → `game_content_asset` + `content_kind` | Same envelope: stable_id, path, display_name_key, UnityEngine.Object |
| `sprite_asset` | `material_asset` | **88** | **Merge** → `game_content_asset` | Same pattern; only path column name differs |
| `prefab_asset` | `material_asset` | **85** | **Merge** → `game_content_asset` | Same |
| `building` (buildings) | `building_group` (building_groups) | **82** | **Unify** under `building_group` + optional `building_display_profile` | Same 67 `source_guid` families; buildings=plain keys, groups=LazyText; duplicate stable_id per file |
| `building_simulation_setting` | `building_group_simulation_setting` | **90** | **Merge** → `building_simulation_setting` on unified group | Same simulation_parameters fields |
| `building_localization_overlay` | `building_group_localization_ref` | **85** | **Merge** | Both store LazyText keys for same groups |
| `building_group_member` (buildings) | `building_group_member` (building_groups) | **92** | **Merge** — one table; FK to unified group | Same Definitions[] semantics |
| `building_variant` (building_variants) | `building_variant` (belts_pipes_transport snapshot) | **75** | **Keep separate import** — transport file is byte-equal snapshot, not second owner | Same schema path; single canonical import from building_variants |
| `export_incomplete_section` | `localization_export_status` | **72** | **Relate** — keep both; l10n status is specialization | translations section ⊆ incomplete_sections |
| `game_data_import_batch` | `game_data_import_batch` (all reports) | **100** | Already unified | Identical purpose every report |
| `unknown_property` | `unknown_property` (all) | **100** | Already unified | — |
| `source_object_record` | per-file audit rows | **70** | Optional merge into generic `source_row_audit` | Same shape, different source_file |
| `ResearchNode` (diagram examples) | `research_milestone` | **55** | **Keep separate** | Example diagrams only; no ResearchNode table proposed |
| `building` | `building_variant` | **45** | **Keep separate** | Group vs internal geometry — different lifecycle |
| `transport_building_registry` | `building_variant` | **50** | **Keep separate** | Kind-level registry vs full variant |
| `simulation_system_entry` | `building_variant_custom_config` | **40** | **Keep separate** | System registration vs per-variant config |
| `toolbar_building_placement` | `building` | **48** | **Keep separate** | UI placement row vs group definition |
| `asset_meta_reference` | `prefab_asset` | **35** | **Keep separate** | Meta vs content layer |
| `clr_type_registry_entry` | `shape_component_kind` | **25** | **Keep separate** | CLR catalog vs game subpart enum |

---

## High-confidence merges (action list)

1. **`game_content_asset`** replaces `prefab_asset`, `sprite_asset`, `material_asset` (add `content_kind` enum).
2. **`shape_recipe` family** — one importer, two JSON path profiles (`items` vs `shapes`).
3. **`building_group`** as canonical group table; deprecate parallel `building` table or map 1:1 with `profile=plain|lazy`.
4. **`building_simulation_setting`** — single table keyed by unified group id.
5. **`building_group_member`** — single membership table.
""",
    "03_cross_reference_graph.md": r"""# Cross-Reference Graph

Legend: **confirmed** = documented FK or unique key join; **inferred** = naming/text/hash; **missing** = should link, no key in dump; **ambiguous** = multiple targets.

```text
game_data_import_batch
 ├── has many → game_data_artifact_checksum (confirmed)
 ├── has many → export_warning (confirmed)
 ├── has many → export_incomplete_section (confirmed)
 ├── has one  → localization_export_status (confirmed)
 └── parent of → all domain tables (confirmed)

game_content_asset  [prefab|sprite|material unified]
 └── referenced by → asset_meta_reference (confirmed: ref_stable_id + asset_kind)

asset_meta_reference
 ├── meta_stable_id (unique)
 └── content_stable_id + asset_kind → game_content_asset (confirmed)

building_group  [unified target; today: building + building_group reports]
 ├── has many → building_group_member (confirmed)
 ├── has many → building_placement_rule (confirmed)
 ├── has one  → building_simulation_setting (confirmed)
 ├── has one  → building_localization_overlay (inferred merge)
 └── has many → building_variant via member (confirmed)

building_variant  [canonical: building_variants.json]
 ├── has many → building_connector (confirmed)
 ├── has many → building_footprint_tile (confirmed)
 ├── referenced by → transport_building_registry.transport_kind (inferred text)
 ├── referenced by → toolbar_building_placement.building_definition_key (inferred name = internal_name)
 └── referenced by → simulation_systems text / connectable Building.Definition (missing stable FK)

building_connector
 └── belongs to → building_variant (confirmed)

shape_recipe  [shapes.json authoritative; items.json subset]
 ├── has many → shape_recipe_layer (confirmed)
 │     └── has many → shape_quadrant_slot (confirmed)
 │           ├── FK → shape_component_kind (confirmed)
 │           └── FK → fluid_color (confirmed)
 ├── referenced by → research_unlock_cost.shape_hash (confirmed: 253/253 resolved)
 └── used in → asteroid_lab layout T field (inferred; not same as Hash always)

fluid_color
 └── imported from → fluids.json (confirmed)

research_upgrade
 ├── referenced by → research_prerequisite (confirmed)
 ├── referenced by → global_belt_speed_policy.research_upgrade_key (confirmed: BeltSpeed)
 └── inferred unlocks → building_group / toolbar (ambiguous; SG_* keys only)

research_milestone / research_side_quest / research_side_upgrade
 ├── has many → research_unlock_cost (confirmed)
 ├── has many → research_unlock_reward (confirmed)
 └── has many → research_prerequisite (confirmed)

research_mechanic
 └── referenced by → research_prerequisite + toolbar_group_node (inferred)

toolbar_element
 ├── tree via → toolbar_tree_edge (confirmed)
 ├── BuildingBased → toolbar_building_placement (confirmed)
 ├── IslandBased → toolbar_island_placement (confirmed)
 └── icon_sprite_name → sprite_asset.sprite_path (inferred)

simulation_system_entry
 ├── optional → simulation_factory_stub (confirmed)
 ├── optional → simulation_runtime_audit (confirmed)
 └── global_belt_speed_policy (singleton per batch) → research_upgrade (confirmed)

clr_type_registry_entry
 └── optional lookup ← dumps.source_type_name (inferred; assembly ambiguous)

localized_message  [empty]
 └── should resolve → LazyLocalizedText keys in building_group, toolbar (missing)
```

---

## Research / unlock flow (domain-level)

```text
research_mechanic
 └── gates → research_milestone / side_quest (confirmed prereq)

research_upgrade (upgrade_key)
 └── inferred unlocks → building_group_member / toolbar placement (missing FK)

research_unlock_cost
 └── requires → shape_recipe.shape_hash (confirmed)
```

---

## Transport / belt slice

```text
transport_building_registry
 └── shares snapshot with → building_variant rows in belts_pipes_transport.json (confirmed byte-equal)
       └── same as → building_variants canonical rows (confirmed)
```

---

## Missing link summary

| From | To | Status |
| ---- | -- | ------ |
| `toolbar_building_placement` | `building_variant` | **inferred** (Id.Id) |
| `building_group` | `building_group` duplicate table `building` | **ambiguous** — merge |
| `Building.Definition` in simulation dump | `building_variant` | **missing** |
| `display_name_key` | `localized_message` | **missing** (empty translations) |
| `research_upgrade` | `building` unlock | **inferred** |
""",
    "04_schema_drift.md": r"""# Schema Drift Audit

Same concept modeled differently across per-file reports.

| Concept | Report A | Report B | Drift type | Recommendation |
| ------- | -------- | -------- | ---------- | -------------- |
| Buildable group entity | `building` (buildings) — `group_key` from `source_guid` | `building_group` (building_groups) — `group_key` + LazyText | **Semantic + naming** | Unify to `building_group`; import both files into one table with `display_profile` |
| Group stable id | `building.stable_id` unique per buildings file | `building_group.stable_id` unique per groups file | **Naming** | Same 67 families; store `buildings_stable_id` / `groups_stable_id` as audit columns or prove equality |
| Variant business key | `internal_name` (building_variants) | `Id.Name` in Definitions[] (buildings) | **Naming** | Standardize on `internal_name` |
| Variant stable id | unique per variant row (building_variants) | same stable_id repeated on buildings envelope (67) | **Cardinality** | Only variant table owns geometry; group file stable_id is envelope artifact |
| Shape recipe root path | `definition_snapshot.Definition.*` (items) | `definition_snapshot.*` no Definition wrapper (shapes) | **Structural** | Dual-path normalizer in one importer |
| Shape recipe dump id | `stable_id` **non-unique** (items) | `stable_id` **unique** (shapes) | **ID policy** | Canonical keys: `shape_hash` + `operation_uid` only |
| Content asset path column | `prefab_path` | `sprite_path` / `material_path` | **Naming** | Merge to `content_path` + `content_kind` |
| Meta reference FK | polymorphic `content_stable_id` + `asset_kind` (asset_references) | separate tables in prefabs/sprites/materials reports | **Structural** | asset_references is authoritative for polymorphic FK |
| Simulation setting parent | `building_simulation_setting` → `building_id` | `building_group_simulation_setting` → `building_group_id` | **Naming** | Single table after group unification |
| Toolbar node key | `tree_path` (= display_name_key) | `stable_id` per toolbar row | **Naming** | Use `tree_path` for tree; `stable_id` for dump audit only |
| Research node id | `node_key` from `Id.Id` dict | `upgrade_key` string only on UpgradeId rows | **Structural** | Normalize `Id` dict vs string in DTO layer |
| Research row stable id | unique 268/436 (claimed) but 168 duplicate pairs | — | **ID policy** | Do not use `stable_id` as UK on research tables |
| CLR type id | `dump_stable_id` non-unique (raw_type_index) | — | **ID policy** | UK: `(type_name, assembly_name)` |
| Belt speed research link | `ResearchId: {Id: BeltSpeed}` object | `research_upgrade_key` string column (simulation_systems) | **Naming** | Normalize to `upgrade_key` string |
| Connector role enum | `connector_role` mapped from `$type` (building_variants) | same (belts_pipes_transport) | **Enum** | Single enum table shared |
| Import batch file hash | only `asset_references` hash on batch row (asset_references doc) | per-artifact rows in manifest report | **Cardinality** | `game_data_artifact_checksum` is canonical; drop single `file_hash` on batch or make artifact-specific |
| Localization | `localization_export_status` (translations) | `export_incomplete_section` (manifest) | **Semantic** | Keep both; link by `section_code=translations` |
| Building vs transport flag | `is_transport_building` on building/group | `transport_kind` registry (belts_pipes) | **Semantic** | Related but not duplicate — keep both |
| `display_name_key` | equals path (prefabs/sprites/materials) | LazyText placeholder (building_groups) | **Semantic** | Do not conflate path identity with l10n key |

---

## Type drift watchlist

| Field | Reports | Issue |
| ----- | ------- | ----- |
| `steps_per_tick` | simulation_systems | Documented as numeric `Value` inside object — store as int, not string |
| `PlacerId` | toolbar_entries | Sometimes int, sometimes object — normalize in DTO |
| `Id` on research rows | research_unlocks | dict `{Id: "..."}` vs plain string — normalize to string column |

---

## Cardinality drift

| Relationship | Report A | Report B |
| ------------ | -------- | -------- |
| Group → Variant | 67 groups, 131 variants (building_variants) | buildings Definitions[] cycle refs expand to 131 members |
| Meta → Content | 829 meta → 764+61+4 content (asset_references) | 1:1 per kind |
| Shape recipes | 70 items vs 1170 shapes | strict subset |
""",
    "05_merge_candidates.md": r"""# Merge Opportunities

Requires similar purpose, attributes, lifecycle, and ownership — not name similarity alone.

| Candidate tables | Merge confidence | Recommendation |
| ---------------- | ---------------: | -------------- |
| `prefab_asset` + `sprite_asset` + `material_asset` | **92** | → **`game_content_asset`** with `content_kind` enum (`prefab`,`sprite`,`material`) and shared columns (`stable_id`, `content_path`, `display_name_key`, …) |
| `shape_recipe` / `shape_recipe_layer` / `shape_quadrant_slot` (items + shapes docs) | **98** | Already one model; enforce **single importer module** |
| `building` + `building_group` | **85** | → **`building_group`** canonical; ingest `buildings.json` as `display_profile=plain` or merge keys |
| `building_simulation_setting` + `building_group_simulation_setting` | **88** | → **`building_simulation_setting`** FK to unified group |
| `building_localization_overlay` + `building_group_localization_ref` | **83** | → **`building_localization_overlay`** |
| `building_group_member` (two reports) | **95** | → single **`building_group_member`** with FK to unified group |
| `building_variant` + belts_pipes_transport variant rows | **60** | **Do not merge tables** — same data, import once from `building_variants.json`; belts file is checksum-only duplicate |
| `export_incomplete_section` + `localization_export_status` | **65** | Keep separate; add FK/link `localization_export_status.incomplete_section_id` optional |
| `simulation_runtime_audit` + `unknown_property` | **40** | Keep separate — different retention policies |
| `source_object_record` (planned) + row-level `stable_id` | **55** | Keep `source_object_record` for index; do not duplicate as entity PK |
| `toolbar_group_node` + `toolbar_element` (group kind) | **50** | Keep separate kinds on `toolbar_element.element_kind` instead of merge |
| `research_milestone` + `research_side_quest` + `research_side_upgrade` | **45** | Keep separate node tables (different rules); share `research_unlock_cost` child |
| `connectable_simulation_attachment` + `building_connector` | **35** | **Do not merge** — different abstraction levels |

---

## Post-merge target schema size

~**42** domain tables (down from ~50), excluding audit-only tables.
""",
    "06_missing_cross_references.md": r"""# Missing Cross References

Links that should exist for a coherent planner DB but are absent or only textual in dumps.

| Source | Missing target | Evidence | Confidence |
| ------ | -------------- | -------- | ---------: |
| `toolbar_building_placement` | `building_variant` | `BuildingDefinition.Id.Id` matches `internal_name`; no UUID | **92** |
| `toolbar_building_placement` | `sprite_asset` / `game_content_asset` | `icon_sprite_name` e.g. `BeltIcon` | **88** |
| `research_upgrade` | `building_group` / `building_variant` | `SG_*` / `Milestone_*` keys; textual in building_groups | **75** |
| `research_unlock_reward` | `building_variant` / `research_upgrade` | Reward `$type` variants not fully enum-mapped | **70** |
| `simulation_system_entry` | `building_variant` | Name overlap only; no stable_id | **65** |
| `connectable_simulation_attachment` | `building_variant` | Nested `Building.Definition` blob | **80** |
| `building_group_member` | `building_variant` | FK planned but `building_group_id` empty in variant dump | **85** (import order) |
| `building_variant` | `building_group` | `building_group_id` column nullable, not in JSON | **90** |
| `asset_meta_reference` | `game_content_asset` | Designed FK; must import content before meta | **95** |
| `localized_message` | all LazyText keys | translations.json empty | **95** |
| `shape_recipe` | `shape_component_kind` | Letter code mapping in shape_catalog.py not in DB | **60** |
| `transport_building_registry` | `simulation_system_entry` | transport_kind in simulation text | **55** |
| `research_prerequisite` | `research_milestone` polymorphic parent | Separate tables per node kind — need `research_node` supertype or `parent_kind` | **70** |
| `toolbar_element` | `research_mechanic` | `MechanicRequiredToUnlock` on categories | **78** |
| `global_belt_speed_policy` | `research_upgrade` | Documented; needs FK constraint test | **90** |
| `building_placement_rule` | `building_footprint_tile` | Rules vs geometry — semantic related | **50** |
| `clr_type_registry_entry` | dumps `source_type_name` | Optional validation only | **55** |
| `prefab_asset` | `building_variant` | Prefabs are visual LOD meshes, weak name overlap | **45** |

---

## Recommended FK additions (implementation phase)

1. `toolbar_building_placement.building_variant_id` → `building_variant.id` (resolve via `building_definition_key`).
2. `research_unlock_cost.shape_recipe_id` → `shape_recipe.id` (resolve via `shape_hash`).
3. `asset_meta_reference` polymorphic validator → `game_content_asset`.
4. `building_group_member.building_variant_id` → `building_variant.id` (required after both imports).
5. `building_group_member.building_group_id` → `building_group.id`.
""",
    "07_identifier_audit.md": r"""# ID Policy Audit

| Entity | Issue | Severity | Recommendation |
| ------ | ----- | -------- | -------------- |
| `shape_recipe` (items import) | `stable_id` duplicated across 70 rows | **CRITICAL** | UK: `shape_hash` + `operation_uid`; `stable_id` → `dump_stable_id` non-unique |
| `research_unlocks` rows | 168 extra rows sharing 8 `stable_id` values (level + upgrade id pairs) | **HIGH** | UK: `upgrade_key` or (`node_kind`, `node_key`); never UK on `stable_id` alone |
| `clr_type_registry_entry` | `dump_stable_id` not unique (114 collisions) | **HIGH** | UK: (`type_name`, `assembly_name`) |
| `building_variant` | `internal_name` is canonical; `stable_id` is dump hash | **LOW** | UK both; expose `internal_name` to planner |
| `building` / `building_group` | `group_key` (= source_guid) vs per-file `stable_id` | **MEDIUM** | Prove 67 keys align; use `group_key` as business UK |
| `toolbar_element` | `tree_path` unique; `stable_id` unique | **LOW** | UI tree uses `tree_path`; `stable_id` audit only |
| `prefab_asset` / `sprite_asset` / `material_asset` | `stable_id` unique per file | **LOW** | Keep as content UK |
| `asset_meta_reference` | `meta_stable_id` ≠ `content_stable_id` | **LOW** | Both unique; polymorphic join on content + kind |
| `simulation_system_entry` | `simulation_kind_key` repeats 38× for conveyor | **MEDIUM** | UK: `stable_id` OR (`simulation_kind_key`, `source_row_index`) |
| `game_data_import_batch` | `manifest_self_hash` vs composite timestamp key | **LOW** | Prefer `manifest_self_hash` UK |
| All dumps | `instance_id` on Unity objects | **MEDIUM** | Never FK; strip from domain |
| All dumps | `source_type_name` as PK candidate | **CRITICAL** | Store as `dump_source_type` / `element_kind` enum only |
| `display_name_key` `#N` (shapes) | numeric dump labels | **LOW** | Not domain keys |
| `operation_uid` gaps 1–1330 | 1170 shapes use subset of ids | **LOW** | UK still valid on present ids |

---

## Canonical ID policy (recommended global)

| Domain concept | Canonical key | Audit / dump only |
| -------------- | --------------- | ----------------- |
| Import bundle | `manifest_self_hash` | — |
| Shape recipe | `shape_hash` (+ `operation_uid`) | `dump_stable_id` |
| Building group | `group_key` | per-file `stable_id` |
| Building variant | `internal_name` | `stable_id` |
| Content asset | `stable_id` + `content_kind` | — |
| Meta asset | `meta_stable_id` | — |
| Research node | `node_key` + `node_kind` | `stable_id` |
| Research upgrade | `upgrade_key` | `stable_id` |
| Toolbar node | `tree_path` | `stable_id` |
| Simulation entry | `stable_id` (or kind+index) | `clr_type_audit` |
| CLR type | (`type_name`, `assembly_name`) | `dump_stable_id` |
| Localized string | (`message_key`, `locale_code`) | — |
""",
    "08_runtime_leakage.md": r"""# Runtime Metadata Leakage Audit

Fields that must remain audit/source columns, not domain entities.

| Runtime field / pattern | Appears in | Risk | Recommendation |
| ----------------------- | ---------- | ---- | -------------- |
| `AtomicStatefulIslandSimulationSystem`2[[Game.Content…, Version=0.0.0.0, PublicKeyToken=null], …]` | simulation_systems | **CRITICAL** if promoted to entity | `simulation_system_entry.clr_type_audit` TEXT only |
| `Game.Core.Research.ResearchUpgradeId` | research_unlocks | **HIGH** | Row discriminator → `element_kind`; table `research_upgrade` |
| `BuildingBasedPlacementToolbarElementData` | toolbar_entries | **HIGH** | `toolbar_element.element_kind` enum |
| `ShapeItem` / `ShapeDefinition` | items, shapes | **HIGH** | `dump_source_type`; domain is `shape_recipe` |
| `UnityEngine.Object` | prefabs, sprites, materials, many envelopes | **MEDIUM** | `dump_source_type` column |
| `asset.meta` / `UnityEngine.Object` (meta) | asset_references | **MEDIUM** | `dump_source_type` on meta row |
| `IPresentableToolbarElementData.Icon` | toolbar_entries | **HIGH** if column name used | Extract `icon_sprite_name` only |
| `ISimulationSystem.OnSimulationCreated` | simulation_systems | **CRITICAL** | `simulation_runtime_audit` or drop |
| `<*k__BackingField>` | research_unlocks, building_groups, many | **HIGH** | Strip on import; `unknown_property` if needed |
| `$type` | all nested snapshots | **MEDIUM** | Map to enum tables; never table per `$type` |
| `$unity` + `instance_id` | items, shapes, toolbar, building_groups | **HIGH** | Never store `instance_id` as FK |
| `Core.Localization.LazyLocalizedText` | building_groups, toolbar | **MEDIUM** | Store resolved `message_key` only |
| `LazyLocalizedTextPlaceholderResolver` | building_groups | **MEDIUM** | l10n infrastructure, not domain entity |
| `Game.Content.*` assembly strings | raw_type_index | **MEDIUM** | `assembly_name` bucket only |
| `ResearchUnlockManager` | research_unlocks | **HIGH** | Singleton → `research_global_config` + layout index, not a entity table |
| `ToolbarSlotSeparator` as table name | toolbar_entries | **MEDIUM** | `toolbar_element.element_kind=separator` |
| `#166` / memory-style ids | not observed in exports | **LOW** | Reject if appear |

---

## Correct placement tier

| Tier | Store as |
| ---- | -------- |
| Domain tables | Game meaning only (variant, recipe, upgrade, …) |
| `unknown_property` | Unmapped keys |
| `simulation_runtime_audit` / `source_object_record` | Opaque captures |
| Import batch tables | Manifest + hashes + warnings |

---

## Reports with strongest leakage discipline

Best: **asset_references**, **prefabs**, **sprites**, **materials**, **fluids**, **manifest**  
Needs enforcement: **simulation_systems**, **toolbar_entries**, **research_unlocks**
""",
    "09_final_canonical_schema.md": r"""# Final Canonical Schema Recommendation

Unified domain model for `game_data` imports.  
**Source report structure ≠ final DB structure.**

Status: **Approved** | **Needs review** | **Rejected**

---

## Layer 0 — Import & integrity

### `game_data_import_batch` — **Approved**

| Column | Constraints |
| ------ | ----------- |
| `id` | PK |
| `manifest_self_hash` | UNIQUE |
| `game_version`, `unity_version`, `dump_mod_version`, `dump_schema_version` | |
| `dump_timestamp_utc`, `source_method` | |
| `imported_at` | inferred |

**Origins:** all reports, manifest.

### `game_data_artifact_checksum` — **Approved**

UK: `(import_batch_id, artifact_filename)`. Columns: `expected_sha256`, `import_status`, `is_incomplete`.

**Origins:** manifest.

### `export_warning`, `export_incomplete_section` — **Approved**

**Origins:** manifest.

### `localization_export_status` — **Approved** (Needs review link to incomplete)

**Origins:** translations, manifest.

### `source_object_record`, `unknown_property` — **Approved**

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

### `simulation_system_entry` + stubs — **Approved**

Children: `simulation_factory_stub`, `global_belt_speed_policy`, `connectable_simulation_attachment` (review), `simulation_runtime_audit` (JSON audit only).

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
| simulation_systems | simulation_system_entry* |
| toolbar_entries | toolbar_* |
| translations | localization_export_status |
| raw_type_index | clr_type_registry_entry |
| items | subset upsert into shape_recipe* |
| belts_pipes_transport | transport_building_registry + checksum only (no second variant import) |
""",
}


def main() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    for name, body in FILES.items():
        (AUDIT / name).write_text(body.strip() + "\n", encoding="utf-8")
        print("wrote", name)


if __name__ == "__main__":
    main()
