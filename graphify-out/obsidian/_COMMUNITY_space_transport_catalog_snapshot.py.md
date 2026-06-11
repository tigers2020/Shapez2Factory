---
type: community
cohesion: 0.15
members: 26
---

# space_transport_catalog_snapshot.py

**Cohesion:** 0.15 - loosely connected
**Members:** 26 nodes

## Members
- [[.__init__()_16]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[.from_file()_2]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[.from_payload()_2]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[.lookup_io()]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[.lookup_tile_id()]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[.to_payload()]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[CommittedRoute]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py
- [[EswmMask]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py
- [[Project committed routes to SpaceBeltSpacePipe tiles via catalog lookup.]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py
- [[ProjectedTransportTile]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py
- [[SpaceTransportCatalogInvalid]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[SpaceTransportCatalogIssue]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[SpaceTransportTileCatalog_1]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[SpaceTransportTileCatalogEntry]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[TransportIoSignature]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[_dirs_from_mask()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py
- [[_entry_to_dict()]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[_heuristic_tile_id_and_rotation()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py
- [[_mask_for_dirs()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py
- [[_parse_bool_mask()]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[_parse_entry()_1]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[_signature_for_cell()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py
- [[``SpaceTransportTileCatalog`` — frozen JSON export of island transport tiles (no]] - rationale - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[project_routes_to_tiles()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py
- [[space_transport_catalog_snapshot.py]] - code - src/shapez2_factory/adapters/asteroid_lab/space_transport_catalog_snapshot.py
- [[sprite_projector.py]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sprite_projector.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/space_transport_catalog_snapshotpy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_ReplayEventType]]
- 1 edge to [[_COMMUNITY_Coord]]
- 1 edge to [[_COMMUNITY_Path]]
- 1 edge to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_Exception]]
- 1 edge to [[_COMMUNITY_run_layers_02_to_06()]]
- 1 edge to [[_COMMUNITY_Enum]]
- 1 edge to [[_COMMUNITY_route_layer04_sequential()]]

## Top bridge nodes
- [[project_routes_to_tiles()]] - degree 7, connects to 2 communities
- [[space_transport_catalog_snapshot.py]] - degree 10, connects to 1 community
- [[SpaceTransportCatalogInvalid]] - degree 9, connects to 1 community
- [[_signature_for_cell()]] - degree 5, connects to 1 community
- [[.from_file()_2]] - degree 4, connects to 1 community