# Schema Drift Audit

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
