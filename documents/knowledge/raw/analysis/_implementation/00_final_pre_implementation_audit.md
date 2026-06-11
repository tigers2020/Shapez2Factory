# Final Pre-Implementation Audit

Verified against **153** analysis reports, **9** `_audit/` files, and `documents/game_data/*.json`.

| Finding | Source report | Decision | Applied to model | Notes |
| ------- | ------------- | -------- | ---------------- | ----- |
| Merge prefab/sprite/material | `_audit/02`, `09` | **Approved** → `GameContentAsset` | `GameContentAsset` + `content_kind` | Single table |
| Unify building + building_group | `_audit/02`, `04` | **Approved** → `BuildingGroup` | `BuildingGroup.display_profile` | `plain` / `lazy_overlay` |
| shape_recipe dual path | items, shapes | **Approved** one table | `ShapeRecipe` | `catalog_source` field |
| items stable_id non-unique | `_audit/07` | **Rejected as UK** | `source_stable_id` only | UK: `canonical_id` from hash+uid |
| research stable_id duplicates | `_audit/07` | **Rejected as UK** | `source_stable_id` | UK: `upgrade_key` / `node_key` |
| CLR type stable_id collisions | `_audit/07` | **Rejected as UK** | `source_stable_id` | UK: `(type_name, assembly_name)` |
| belts duplicate variant import | `_audit/05` | **Skip variant re-import** | `TransportBuildingRegistry` only | Variants from `building_variants.json` |
| simulation CLR strings | `_audit/08` | **Audit only** | `SimulationRuntimeAudit.audit_blob` | JSONField allowed here only |
| translations empty | translations | **Status row only** | `LocalizationExportStatus` | No `LocalizedMessage` rows |
| toolbar FK to variant | `_audit/06` | **Resolved on import** | `ToolbarBuildingPlacement.building_variant` FK | Match `internal_name` |
| research cost → shape | `_audit/03` | **FK** | `ResearchUnlockCost.shape_recipe` | Resolve by `shape_hash` |
| asset meta before content | `_audit/06` | **Import order** | pipeline step 6–7 | Enforced in importer |
| UnknownProperty not raw_json | all | **Approved** | `UnknownProperty` | preview + hash only |
| Per-$type tables | `_audit/09` | **Rejected** | `element_kind` enums | Discriminators on rows |
| building_variant_custom_config | building_variants | **Defer structured** | optional model later | Not in v1 importer |
| progression_layout_index | research | **Needs review** | omitted v1 | Open in `04` |

## Checklist

- [x] every json_file_name report read (17 stems)
- [x] every _audit report read (01–09)
- [x] duplicate entity recommendations applied
- [x] merge candidates resolved
- [x] schema drift handled via canonical_id policy
- [x] missing cross references handled in importer
- [x] identifier audit applied
- [x] runtime leakage rejected from domain models
