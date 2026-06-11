---
type: community
cohesion: 0.08
members: 45
---

# DecodedCellDTO

**Cohesion:** 0.08 - loosely connected
**Members:** 45 nodes

## Members
- [[4-neighbor helpers for transport component grouping (A6; ORM-free).]] - rationale - src/shapez2_factory/domain/asteroid_lab/transport_components.py
- [[Build lab blueprint root with Extension ``T`` for asteroid field cells.]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[Decode copy string (optional trailing ``$``) and import reconstruction cells.]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[DecodedCellDTO]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[Field-only cells for ``rebuilt_copy_code`` (Extension ``T``, no beltspipesmine]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[Full topology cell set for persist (no replay frame reads).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[Import decoded blueprint then keep only asteroid field cells for game paste.]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[Load cells from ORM row via reconstruction import (full_map ``decoded_json``).]] - rationale - django_apps/asteroid_lab/services/reconstructed_asteroid_service.py
- [[Load reconstructed island cells from persisted ``decoded_json``.]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[Map reconstruction cell to game ``T`` for persisted copyjson (fields Extensio]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[Normalize strippablebuilding tiles to ``asteroid__field`` for game field expor]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[Overlay recon on structural map; keep structural keys absent from ``recon_cells`]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[Post-extension-cleanup cells (replay ``row_extension`` parity).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[Pure cell-level reconstruction-complete merge (PR-CLI-2c display_map split).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[Reconstructed island ``asteroid__field`` ``Layout_MinerExtension`` blueprin]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[Replay-only cell same (x,y,layer) as removed minerextension; not in decode BP.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[Stable ordering; ``None`` layer sorts before negative real layers.]] - rationale - src/shapez2_factory/domain/asteroid_lab/transport_components.py
- [[Stable set for roundtrip tests ``(x, y, layer, cell_kind)``.]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[Transport, miners, and extensions are removed for reconstruction topology.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/evidence.py
- [[_entry_dict_from_cell()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[_field_cell_kind_for_extension()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[_field_cell_kind_for_miner()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[_remap_cell_to_asteroid_field()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[_shell_from_source()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[_synthetic_asteroid_field_cell()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[build_reconstructed_blueprint_root()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[cell_position_key()]] - code - src/shapez2_factory/domain/asteroid_lab/transport_components.py
- [[cells_for_field_export()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[cells_for_field_export_from_decoded_json()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[complete_map_merge.py]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[is_strippable_building()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/evidence.py
- [[is_transport_tile()]] - code - src/shapez2_factory/domain/asteroid_lab/transport_components.py
- [[load_reconstructed_asteroid_cells()]] - code - django_apps/asteroid_lab/services/reconstructed_asteroid_service.py
- [[load_reconstruction_cells_from_copy_code()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[load_reconstruction_cells_from_decoded_json()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[merge_reconstruction_display_cells()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[merged_display_cells_from_reconstruction()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[reconstruction_blueprint_export.py]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[reconstruction_cell_keys()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[replace_extensions_with_synthetic_fields()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[replace_miners_with_synthetic_fields()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[sort_key_xy_layer()]] - code - src/shapez2_factory/domain/asteroid_lab/transport_components.py
- [[structural_cells_from_cleanup()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/complete_map_merge.py
- [[tile_type_for_reconstruction_export()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[transport_components.py]] - code - src/shapez2_factory/domain/asteroid_lab/transport_components.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/DecodedCellDTO
SORT file.name ASC
```

## Connections to other communities
- 11 edges to [[_COMMUNITY_record_existing_layout_inspection_frames]]
- 10 edges to [[_COMMUNITY_stamp_islands_uniform()]]
- 8 edges to [[_COMMUNITY_ReconstructionResult]]
- 8 edges to [[_COMMUNITY_reconstruct_after_cleanup()]]
- 5 edges to [[_COMMUNITY_Any]]
- 5 edges to [[_COMMUNITY_is_asteroid_evidence()]]
- 4 edges to [[_COMMUNITY_build_decoded_blueprint_snapshot()]]
- 3 edges to [[_COMMUNITY_normalize_decoded_blueprint()]]
- 3 edges to [[_COMMUNITY_build_normalized_reconstruction_topology]]
- 3 edges to [[_COMMUNITY_build_reconstruction_complete_map()]]
- 3 edges to [[_COMMUNITY_build_reconstructed_map_persist_payload(]]
- 2 edges to [[_COMMUNITY_SafeString]]
- 2 edges to [[_COMMUNITY_complete_map_serializer.py]]
- 2 edges to [[_COMMUNITY_deconstruct_snapshot()]]
- 1 edge to [[_COMMUNITY_sync_admin_list_thumbnail()]]
- 1 edge to [[_COMMUNITY_build_layer02_timeline_frame_wire_dict()]]
- 1 edge to [[_COMMUNITY_enrich_lab_timeline_frames_with_terrain_]]
- 1 edge to [[_COMMUNITY_decode_copy_string()]]

## Top bridge nodes
- [[DecodedCellDTO]] - degree 65, connects to 14 communities
- [[merged_display_cells_from_reconstruction()]] - degree 10, connects to 4 communities
- [[is_transport_tile()]] - degree 9, connects to 4 communities
- [[reconstruction_blueprint_export.py]] - degree 15, connects to 3 communities
- [[load_reconstruction_cells_from_decoded_json()]] - degree 8, connects to 2 communities