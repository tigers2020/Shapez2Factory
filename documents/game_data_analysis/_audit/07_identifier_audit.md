# ID Policy Audit

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
