---
type: community
cohesion: 0.22
members: 13
---

# build_decoded_blueprint_snapshot()

**Cohesion:** 0.22 - loosely connected
**Members:** 13 nodes

## Members
- [[Build class`DecodedBlueprintSnapshotDTO` from persisted ``decoded_json`` (pure]] - rationale - src/shapez2_factory/domain/asteroid_lab/decoded_blueprint_snapshot.py
- [[Coerce blueprint scalars; ``None`` → ``0`` (same as entry ``get('X', 0)`` style)]] - rationale - src/shapez2_factory/domain/asteroid_lab/decoded_blueprint_snapshot.py
- [[Import ``BP.Entries`` with Extension ``asteroid__field`` (not miner_extension]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[Parse top-level ``BP.Entries`` into cell DTOs and aggregate metadata.      Doe]] - rationale - src/shapez2_factory/domain/asteroid_lab/decoded_blueprint_snapshot.py
- [[Return ``(cell_kind, transport_kind)``; Extension ``T`` asteroid field kinds.]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[Summarize ``B.Entries`` only; do not unfold into world cells.]] - rationale - src/shapez2_factory/domain/asteroid_lab/decoded_blueprint_snapshot.py
- [[_as_int()_1]] - code - src/shapez2_factory/domain/asteroid_lab/decoded_blueprint_snapshot.py
- [[_extract_layer()]] - code - src/shapez2_factory/domain/asteroid_lab/decoded_blueprint_snapshot.py
- [[_nested_b_summary()]] - code - src/shapez2_factory/domain/asteroid_lab/decoded_blueprint_snapshot.py
- [[build_decoded_blueprint_snapshot()]] - code - src/shapez2_factory/domain/asteroid_lab/decoded_blueprint_snapshot.py
- [[cell_kind_for_reconstruction_import()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[decoded_blueprint_snapshot.py]] - code - src/shapez2_factory/domain/asteroid_lab/decoded_blueprint_snapshot.py
- [[entries_to_reconstruction_cells()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_decoded_blueprint_snapshot
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_Any]]
- 4 edges to [[_COMMUNITY_DecodedCellDTO]]
- 2 edges to [[_COMMUNITY_sync_admin_list_thumbnail()]]
- 2 edges to [[_COMMUNITY_build_golden_oracle()]]
- 2 edges to [[_COMMUNITY_entry_island_raw_coord()]]
- 2 edges to [[_COMMUNITY_record_existing_layout_inspection_frames]]
- 1 edge to [[_COMMUNITY_SafeString]]
- 1 edge to [[_COMMUNITY_GeneSeed]]
- 1 edge to [[_COMMUNITY_reconstruct_after_cleanup()]]
- 1 edge to [[_COMMUNITY_deconstruct_snapshot()]]

## Top bridge nodes
- [[build_decoded_blueprint_snapshot()]] - degree 16, connects to 9 communities
- [[entries_to_reconstruction_cells()]] - degree 9, connects to 3 communities
- [[cell_kind_for_reconstruction_import()]] - degree 4, connects to 2 communities
- [[_as_int()_1]] - degree 5, connects to 1 community
- [[_nested_b_summary()]] - degree 5, connects to 1 community