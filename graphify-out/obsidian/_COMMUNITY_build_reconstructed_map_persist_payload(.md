---
type: community
cohesion: 0.16
members: 14
---

# build_reconstructed_map_persist_payload(

**Cohesion:** 0.16 - loosely connected
**Members:** 14 nodes

## Members
- [[Assemble full_map lab copy + JSON from reconstructioncleanup (no replay IO).]] - rationale - django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py
- [[Build full_map lab JSON + copy string for ``ReconstructedAsteroidMap`` persisten]] - rationale - django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py
- [[ORM-ready payload original snapshot + full_map reconstruction (no replay reads)]] - rationale - django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py
- [[Persist and load topology-reconstructed asteroid maps (ORM + blueprint adapter).]] - rationale - django_apps/asteroid_lab/services/reconstructed_asteroid_service.py
- [[Re-run reconstruction and overwrite the persisted map row for ``run_key``.]] - rationale - django_apps/asteroid_lab/services/reconstructed_asteroid_service.py
- [[ReconstructedMapPersistPayload]] - code - django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py
- [[Write or update ``ReconstructedAsteroidMap`` for ``(map_input, run_key)``.]] - rationale - django_apps/asteroid_lab/services/reconstructed_asteroid_service.py
- [[``SHAPEZ2-4-` with trailing ``$`` (game paste convention).]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[build_reconstructed_map_persist_payload()]] - code - django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py
- [[encode_reconstructed_copy_string()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[persist_reconstructed_asteroid_map()]] - code - django_apps/asteroid_lab/services/reconstructed_asteroid_service.py
- [[reconstructed_asteroid_service.py]] - code - django_apps/asteroid_lab/services/reconstructed_asteroid_service.py
- [[reconstructed_map_persist_builder.py]] - code - django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py
- [[refresh_reconstructed_map_for_map_input()]] - code - django_apps/asteroid_lab/services/reconstructed_asteroid_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_reconstructed_map_persist_payload
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_record_existing_layout_inspection_frames]]
- 3 edges to [[_COMMUNITY_Any]]
- 3 edges to [[_COMMUNITY_DecodedCellDTO]]
- 3 edges to [[_COMMUNITY_ReconstructionResult]]
- 1 edge to [[_COMMUNITY_normalize_decoded_blueprint()]]
- 1 edge to [[_COMMUNITY_decode_copy_string()]]
- 1 edge to [[_COMMUNITY_sync_admin_list_thumbnail()]]
- 1 edge to [[_COMMUNITY_build_initial_replay_for_map_input()]]

## Top bridge nodes
- [[build_reconstructed_map_persist_payload()]] - degree 11, connects to 5 communities
- [[persist_reconstructed_asteroid_map()]] - degree 9, connects to 5 communities
- [[encode_reconstructed_copy_string()]] - degree 5, connects to 3 communities
- [[reconstructed_asteroid_service.py]] - degree 5, connects to 2 communities
- [[refresh_reconstructed_map_for_map_input()]] - degree 4, connects to 1 community