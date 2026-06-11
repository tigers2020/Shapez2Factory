# Cross-Reference Graph

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
