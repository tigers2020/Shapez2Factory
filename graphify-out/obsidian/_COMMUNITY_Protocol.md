---
type: community
cohesion: 0.07
members: 29
---

# Protocol

**Cohesion:** 0.07 - loosely connected
**Members:** 29 nodes

## Members
- [[.apply()]] - code - django_apps/shapez_core/domain/operation.py
- [[.decode()]] - code - src/shapez2_factory/application/asteroid_lab/ports/copy_decode.py
- [[.emit()_1]] - code - src/shapez2_factory/domain/asteroid_lab/observability/boundary_sink.py
- [[.emit()_2]] - code - src/shapez2_factory/domain/asteroid_lab/observability/boundary_sink.py
- [[.lookup_io()_1]] - code - src/shapez2_factory/application/asteroid_lab/ports/space_transport_catalog.py
- [[.lookup_tile_id()_1]] - code - src/shapez2_factory/application/asteroid_lab/ports/space_transport_catalog.py
- [[Apply this operation to one or more input shapes.]] - rationale - django_apps/shapez_core/domain/operation.py
- [[BoundaryTraceSink_1]] - code - src/shapez2_factory/domain/asteroid_lab/observability/boundary_sink.py
- [[CopyDecodePort]] - code - src/shapez2_factory/application/asteroid_lab/ports/copy_decode.py
- [[DecodedCopy]] - code - src/shapez2_factory/application/asteroid_lab/ports/copy_decode.py
- [[No-op sink used by default so core stays side-effect free.]] - rationale - src/shapez2_factory/domain/asteroid_lab/observability/boundary_sink.py
- [[NullBoundaryTraceSink]] - code - src/shapez2_factory/domain/asteroid_lab/observability/boundary_sink.py
- [[Operation]] - code - django_apps/shapez_core/domain/operation.py
- [[Pair cells by ``(x, y, layer)`` and list ``cell_kind`` changes (for boundary pay]] - rationale - src/shapez2_factory/domain/asteroid_lab/observability/boundary_sink.py
- [[Placeholder decoded copy payload; full DTO lands in PR-CLI-2a.]] - rationale - src/shapez2_factory/application/asteroid_lab/ports/copy_decode.py
- [[Port for Layer 04 space beltpipe tile catalog (no raw game JSON in core L4).]] - rationale - src/shapez2_factory/application/asteroid_lab/ports/space_transport_catalog.py
- [[Protocol]] - code
- [[Pure boundary observability seam (no Django, no settings, no file IO).  The d]] - rationale - src/shapez2_factory/domain/asteroid_lab/observability/boundary_sink.py
- [[Receives one boundary record built by a pure pipeline stage.]] - rationale - src/shapez2_factory/domain/asteroid_lab/observability/boundary_sink.py
- [[Resolve tile by ESWN IO signature at R0_E_CW.]] - rationale - src/shapez2_factory/application/asteroid_lab/ports/space_transport_catalog.py
- [[Resolve tile by island layout id (``SpaceBelt_Forward``, etc.).]] - rationale - src/shapez2_factory/application/asteroid_lab/ports/space_transport_catalog.py
- [[SpaceTransportCatalogPort]] - code - src/shapez2_factory/application/asteroid_lab/ports/space_transport_catalog.py
- [[SpaceTransportTileCatalogEntry_1]] - code - src/shapez2_factory/application/asteroid_lab/ports/space_transport_catalog.py
- [[``CopyDecodePort`` decode a shapez2 copy string into a pure payload.  The fu]] - rationale - src/shapez2_factory/application/asteroid_lab/ports/copy_decode.py
- [[boundary_sink.py]] - code - src/shapez2_factory/domain/asteroid_lab/observability/boundary_sink.py
- [[copy_decode.py]] - code - src/shapez2_factory/application/asteroid_lab/ports/copy_decode.py
- [[operation.py]] - code - django_apps/shapez_core/domain/operation.py
- [[space_transport_catalog.py]] - code - src/shapez2_factory/application/asteroid_lab/ports/space_transport_catalog.py
- [[summarize_cell_kind_transitions()]] - code - src/shapez2_factory/domain/asteroid_lab/observability/boundary_sink.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Protocol
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_pattern_bundle_highlight.py]]
- 1 edge to [[_COMMUNITY_GraphPreviewRenderer]]
- 1 edge to [[_COMMUNITY_json_snapshot_rules.py]]
- 1 edge to [[_COMMUNITY_Shape]]
- 1 edge to [[_COMMUNITY_reconstruct_after_cleanup()]]

## Top bridge nodes
- [[Protocol]] - degree 7, connects to 3 communities
- [[summarize_cell_kind_transitions()]] - degree 4, connects to 2 communities
- [[.apply()]] - degree 3, connects to 1 community
- [[.emit()_1]] - degree 2, connects to 1 community
- [[.emit()_2]] - degree 2, connects to 1 community