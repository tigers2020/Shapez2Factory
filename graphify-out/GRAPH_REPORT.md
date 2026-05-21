# Graph Report - f:\Python_Projects\shapez2Factory\django_apps\game_data  (2026-05-21)

## Corpus Check
- Corpus is ~20,162 words - fits in a single context window. You may not need a graph.

## Summary
- 581 nodes · 1204 edges · 52 communities (24 shown, 28 thin omitted)
- Extraction: 59% EXTRACTED · 41% INFERRED · 0% AMBIGUOUS · INFERRED: 488 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Django Admin Layer|Django Admin Layer]]
- [[_COMMUNITY_JSON Import Pipeline|JSON Import Pipeline]]
- [[_COMMUNITY_Simulation Enums|Simulation Enums]]
- [[_COMMUNITY_Canonical DTOs|Canonical DTOs]]
- [[_COMMUNITY_Simulation Systems Import|Simulation Systems Import]]
- [[_COMMUNITY_Localization Models|Localization Models]]
- [[_COMMUNITY_Admin Browse Registry|Admin Browse Registry]]
- [[_COMMUNITY_Building Models|Building Models]]
- [[_COMMUNITY_Commands & Guards|Commands & Guards]]
- [[_COMMUNITY_Simulation Speed Import|Simulation Speed Import]]
- [[_COMMUNITY_Assets & Provenance|Assets & Provenance]]
- [[_COMMUNITY_Toolbar & Content|Toolbar & Content]]
- [[_COMMUNITY_Export Audit Models|Export Audit Models]]
- [[_COMMUNITY_Cross References|Cross References]]
- [[_COMMUNITY_Lazy Text Parser|Lazy Text Parser]]
- [[_COMMUNITY_Type Classifiers|Type Classifiers]]
- [[_COMMUNITY_CLR Type Registry|CLR Type Registry]]
- [[_COMMUNITY_Browse UI Templates|Browse UI Templates]]
- [[_COMMUNITY_Toolbar Migrations|Toolbar Migrations]]
- [[_COMMUNITY_Cluster 19|Cluster 19]]
- [[_COMMUNITY_Cluster 20|Cluster 20]]
- [[_COMMUNITY_Cluster 21|Cluster 21]]
- [[_COMMUNITY_Cluster 22|Cluster 22]]
- [[_COMMUNITY_Cluster 23|Cluster 23]]
- [[_COMMUNITY_Cluster 24|Cluster 24]]
- [[_COMMUNITY_Cluster 25|Cluster 25]]
- [[_COMMUNITY_Cluster 26|Cluster 26]]
- [[_COMMUNITY_Cluster 27|Cluster 27]]
- [[_COMMUNITY_Cluster 28|Cluster 28]]
- [[_COMMUNITY_Cluster 29|Cluster 29]]
- [[_COMMUNITY_Cluster 30|Cluster 30]]
- [[_COMMUNITY_Cluster 31|Cluster 31]]
- [[_COMMUNITY_Cluster 32|Cluster 32]]
- [[_COMMUNITY_Cluster 33|Cluster 33]]
- [[_COMMUNITY_Cluster 34|Cluster 34]]
- [[_COMMUNITY_Cluster 35|Cluster 35]]
- [[_COMMUNITY_Cluster 36|Cluster 36]]
- [[_COMMUNITY_Cluster 37|Cluster 37]]
- [[_COMMUNITY_Cluster 38|Cluster 38]]
- [[_COMMUNITY_Cluster 39|Cluster 39]]
- [[_COMMUNITY_Cluster 40|Cluster 40]]
- [[_COMMUNITY_Cluster 41|Cluster 41]]
- [[_COMMUNITY_Cluster 42|Cluster 42]]
- [[_COMMUNITY_Cluster 43|Cluster 43]]
- [[_COMMUNITY_Cluster 44|Cluster 44]]
- [[_COMMUNITY_Cluster 45|Cluster 45]]
- [[_COMMUNITY_Cluster 46|Cluster 46]]

## God Nodes (most connected - your core abstractions)
1. `RelatedChangelistSpec` - 82 edges
2. `AggregateRootSpec` - 82 edges
3. `ImportBatch` - 71 edges
4. `SourceObject` - 65 edges
5. `GameDataReadOnlyAdminMixin` - 58 edges
6. `_slug()` - 34 edges
7. `BuildingVariant` - 31 edges
8. `GameDataImporter` - 27 edges
9. `ResearchUpgrade` - 26 edges
10. `SimulationAuditIssueCode` - 21 edges

## Surprising Connections (you probably didn't know these)
- `related_subtable_links()` --calls--> `related_changelist_url()`  [INFERRED]
  admin.py → browse/registry.py
- `SimulationClrProvenance` --uses--> `SimulationAuditIssueCode`  [INFERRED]
  models/simulation.py → enums.py
- `SimulationSystemParameterOccurrence` --uses--> `SimulationAuditIssueCode`  [INFERRED]
  models/simulation.py → enums.py
- `SimulationClrProvenance` --uses--> `SimulationAuditSeverity`  [INFERRED]
  models/simulation.py → enums.py
- `SimulationSystemParameterOccurrence` --uses--> `SimulationAuditSeverity`  [INFERRED]
  models/simulation.py → enums.py

## Communities (52 total, 28 thin omitted)

### Community 0 - "Django Admin Layer"
Cohesion: 0.06
Nodes (87): AggregateRootSpec, Sub-table reached via filtered changelist (no direct FK inline)., Expected parent-centered admin navigation for an aggregate root model., RelatedChangelistSpec, _aggregate_spec(), ArtifactChecksumAdmin, ArtifactChecksumInline, AssetMetaReferenceAdmin (+79 more)

### Community 1 - "JSON Import Pipeline"
Cohesion: 0.07
Nodes (29): dig(), ImportContext, parse_toolbar_child_index(), Shared importer utilities., Last ``Children[n]`` segment in a flattened toolbar ``display_name_key`` path., Upsert row-level provenance; UK remains (batch, file, row_index)., GameDataImporter, Deterministic game_data JSON importer. (+21 more)

### Community 2 - "Simulation Enums"
Cohesion: 0.11
Nodes (26): SimulationAuditIssueCode, SimulationAuditSeverity, BuildingVariant, ResearchUpgrade, Classification, ConnectableSimulation, GlobalBeltSpeedPolicy, Meta (+18 more)

### Community 3 - "Canonical DTOs"
Cohesion: 0.10
Nodes (41): canonical_building_group(), canonical_building_variant(), canonical_clr_type(), canonical_component_kind(), canonical_connectable_simulation(), canonical_connector(), canonical_content_asset(), canonical_fluid_color() (+33 more)

### Community 4 - "Simulation Systems Import"
Cohesion: 0.08
Nodes (34): _bounds_coords(), _building_internal_name(), _ensure_profile(), _import_connectable_attachment(), import_simulation_systems(), Import simulation_systems.json into C-lite normalized models., _set_connector_property(), build_connectable_key() (+26 more)

### Community 5 - "Localization Models"
Cohesion: 0.11
Nodes (16): LazyLocalizedPlaceholderReplacement, LazyLocalizedTextRef, LocalizedMessage, Meta, Canonical game_data domain models (see documents/game_data_analysis/_audit/09)., Normalized Core.Localization.LazyLocalizedText from export snapshots., Meta, ParentKind (+8 more)

### Community 6 - "Admin Browse Registry"
Cohesion: 0.12
Nodes (22): admin_inline_class_names(), aggregate_root_model_labels(), BrowseNamespaceGroup, BrowseSectionEntry, build_browse_groups(), changelist_url_for_model(), Bounded-context browse registry: taxonomy → admin targets and aggregate roots., Return human-readable errors when taxonomy sections lack admin browse targets. (+14 more)

### Community 7 - "Building Models"
Cohesion: 0.12
Nodes (14): BuildingConnector, BuildingFootprintTile, BuildingGroup, BuildingGroupMember, BuildingLocalizationOverlay, BuildingPlacementRule, BuildingSimulationSetting, DisplayProfile (+6 more)

### Community 8 - "Commands & Guards"
Cohesion: 0.10
Nodes (16): BaseCommand, Command, Import normalized game_data from JSON bundle., Migration, validate_before_legacy_drop(), validate_simulation_schema(), RuntimeError, assert_game_data_migrations_applied() (+8 more)

### Community 9 - "Simulation Speed Import"
Cohesion: 0.16
Nodes (20): _import_global_belt_policy_from_buffable(), import_simulation_speeds(), Import simulation_parameters speed keys into typed per-system tables., _record_speed_import_issue(), _resolve_research_upgrade(), classify_speed_entry(), dump_type_name(), parameter_matches_route() (+12 more)

### Community 10 - "Assets & Provenance"
Cohesion: 0.13
Nodes (13): AssetMetaReference, ContentKind, Meta, Canonical game_data domain models (see documents/game_data_analysis/_audit/09)., Row-level provenance for a JSON array element (canonical: ``source_object_record, SourceObject, CatalogSource, FluidColor (+5 more)

### Community 11 - "Toolbar & Content"
Cohesion: 0.21
Nodes (10): GameContentAsset, ResearchMechanic, ElementKind, Meta, Canonical game_data domain models (see documents/game_data_analysis/_audit/09)., ToolbarBuildingPlacement, ToolbarElement, ToolbarIslandPlacement (+2 more)

### Community 12 - "Export Audit Models"
Cohesion: 0.13
Nodes (9): ArtifactChecksum, ExportIncompleteSection, ExportWarning, LocalizationExportStatus, Meta, Canonical game_data domain models (see documents/game_data_analysis/_audit/09)., Ignored or unmapped import field (canonical: ``unknown_property``; not ``GameDat, Per source JSON file in the bundle (canonical: ``game_data_artifact_checksum``). (+1 more)

### Community 13 - "Cross References"
Cohesion: 0.29
Nodes (5): GameDataRefKind, Stable enum codes for game_data (no free-form issue/ref strings)., GameDataReference, Meta, Unresolved cross-references during import (staging only).

### Community 14 - "Lazy Text Parser"
Cohesion: 0.52
Nodes (6): _extract_message_key(), LazyLocalizedReplacement, parse_lazy_localized_text(), _parse_replacements(), ParsedLazyLocalizedText, Parse Core.Localization.LazyLocalizedText snapshots from game dumps.

### Community 15 - "Type Classifiers"
Cohesion: 0.33
Nodes (3): Map dump source_type_name strings to domain element kinds., Extract short kind from CLR generic string without using it as canonical_id., simulation_kind_key()

### Community 16 - "CLR Type Registry"
Cohesion: 0.40
Nodes (3): ClrTypeRegistryEntry, Meta, Canonical game_data domain models (see documents/game_data_analysis/_audit/09).

### Community 17 - "Browse UI Templates"
Cohesion: 0.50
Nodes (4): Aggregate Root vs Entity Section Role, GameDataNamespace and GameDataSection Taxonomy, Bounded Context Browse Index, Game Data Browse Admin Entry

### Community 18 - "Toolbar Migrations"
Cohesion: 0.67
Nodes (3): backfill_island_placement_tree_paths(), _child_index(), Migration

## Knowledge Gaps
- **25 isolated node(s):** `ShapeRecipeDTO`, `Migration`, `Migration`, `Migration`, `Migration` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GameDataImporter` connect `JSON Import Pipeline` to `Commands & Guards`, `Canonical DTOs`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `import_simulation_systems()` connect `Simulation Systems Import` to `JSON Import Pipeline`, `Simulation Speed Import`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `InvalidCanonicalIdError` connect `Canonical DTOs` to `Simulation Speed Import`, `JSON Import Pipeline`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 80 inferred relationships involving `RelatedChangelistSpec` (e.g. with `GameDataReadOnlyAdminMixin` and `GameDataAggregateAdminMixin`) actually correct?**
  _`RelatedChangelistSpec` has 80 INFERRED edges - model-reasoned connections that need verification._
- **Are the 80 inferred relationships involving `AggregateRootSpec` (e.g. with `GameDataReadOnlyAdminMixin` and `GameDataAggregateAdminMixin`) actually correct?**
  _`AggregateRootSpec` has 80 INFERRED edges - model-reasoned connections that need verification._
- **Are the 68 inferred relationships involving `ImportBatch` (e.g. with `GameContentAsset` and `ContentKind`) actually correct?**
  _`ImportBatch` has 68 INFERRED edges - model-reasoned connections that need verification._
- **Are the 62 inferred relationships involving `SourceObject` (e.g. with `GameContentAsset` and `ContentKind`) actually correct?**
  _`SourceObject` has 62 INFERRED edges - model-reasoned connections that need verification._