---
type: community
cohesion: 0.06
members: 55
---

# record_existing_layout_inspection_frames

**Cohesion:** 0.06 - loosely connected
**Members:** 55 nodes

## Members
- [[Append cleanup frames plus stepwise reconstruction replay (UI-only; never solver]] - rationale - django_apps/asteroid_lab/services/existing_layout_service.py
- [[Append decode replay frames raw full map, then transport-stripped map + removal]] - rationale - django_apps/asteroid_lab/services/cell_snapshot_service.py
- [[CleanupResult]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[Convert trace events into persisted replay frames (full_map + diff per step).]] - rationale - django_apps/asteroid_lab/replay/reconstruction_frames.py
- [[Decoded blueprint snapshot ORM read, replay frames, optional ``AsteroidCellSnap]] - rationale - django_apps/asteroid_lab/services/cell_snapshot_service.py
- [[DecodedBlueprintSnapshotDTO]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/topology_contract.py
- [[Existing-layout inspection ORM read, replay frames, optional cell snapshot (A6)]] - rationale - django_apps/asteroid_lab/services/existing_layout_service.py
- [[ExistingLayoutInspectionDTO]] - code - django_apps/asteroid_lab/services/existing_layout_service.py
- [[Fill enclosed holes from ``CleanupResult`` walls and bbox.]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[Full-map snapshot steps for lab replay (output-only; not solver input).]] - rationale - django_apps/asteroid_lab/replay/snapshot_map_replay.py
- [[Full_map row list equivalent to replay ``reconstruction_complete``.]] - rationale - django_apps/asteroid_lab/reconstruction/display_map.py
- [[Load ``AsteroidMapInput.decoded_json`` and build a pure snapshot DTO.]] - rationale - django_apps/asteroid_lab/services/cell_snapshot_service.py
- [[Load ``AsteroidMapInput.decoded_json``, build A5 snapshot, inspect (does not mut]] - rationale - django_apps/asteroid_lab/services/existing_layout_service.py
- [[Persist inspection on class`AsteroidCellSnapshot` JSON fields (no migration).]] - rationale - django_apps/asteroid_lab/services/existing_layout_service.py
- [[Persist one class`AsteroidCellSnapshot` compatible with generic JSON fields.]] - rationale - django_apps/asteroid_lab/services/cell_snapshot_service.py
- [[ReconstructionTraceEvent]] - code - django_apps/asteroid_lab/replay/reconstruction_frames.py
- [[Replay helpers load cleanup  deconstruction result for timeline assembly.]] - rationale - django_apps/asteroid_lab/replay/deconstruction_frames.py
- [[Replay helpers topology reconstruction rows and stepwise snapshot events.  ``]] - rationale - django_apps/asteroid_lab/replay/reconstruction_frames.py
- [[Return full_map rows for transport  extractor  extension cleanup and reconstru]] - rationale - django_apps/asteroid_lab/replay/snapshot_map_replay.py
- [[Row dict merge for replay (structural full_map rows + recon overlay).]] - rationale - django_apps/asteroid_lab/reconstruction/display_map.py
- [[Run cleanup + topology reconstruction for one ``AsteroidMapInput``.]] - rationale - django_apps/asteroid_lab/services/reconstructed_asteroid_service.py
- [[Run pre-reconstruction cleanup on a decoded snapshot.]] - rationale - django_apps/asteroid_lab/replay/deconstruction_frames.py
- [[Run pure inspection on an A5 snapshot (no ORM, no replay reads, no reconstructio]] - rationale - django_apps/asteroid_lab/services/existing_layout_service.py
- [[_cell_overlay_with_equipment_bundles()]] - code - django_apps/asteroid_lab/services/existing_layout_service.py
- [[_overlay_cell_dict()]] - code - django_apps/asteroid_lab/services/cell_snapshot_service.py
- [[_snapshot_event_type_for_trace()]] - code - django_apps/asteroid_lab/replay/reconstruction_frames.py
- [[_sort_rows()]] - code - django_apps/asteroid_lab/replay/reconstruction_frames.py
- [[_title_for_trace()]] - code - django_apps/asteroid_lab/replay/reconstruction_frames.py
- [[_trace_marker_row()]] - code - django_apps/asteroid_lab/replay/reconstruction_frames.py
- [[_without_transport()]] - code - django_apps/asteroid_lab/replay/snapshot_map_replay.py
- [[build_cleanup_and_reconstruction_rows()]] - code - django_apps/asteroid_lab/replay/snapshot_map_replay.py
- [[build_decoded_blueprint_snapshot_from_input()]] - code - django_apps/asteroid_lab/services/cell_snapshot_service.py
- [[build_existing_layout_inspection_from_input()]] - code - django_apps/asteroid_lab/services/existing_layout_service.py
- [[build_existing_layout_inspection_from_snapshot()]] - code - django_apps/asteroid_lab/services/existing_layout_service.py
- [[build_reconstruction_replay_events()]] - code - django_apps/asteroid_lab/replay/reconstruction_frames.py
- [[cell_key_xy_layer()]] - code - django_apps/asteroid_lab/replay/snapshot_map_replay.py
- [[cell_snapshot_service.py]] - code - django_apps/asteroid_lab/services/cell_snapshot_service.py
- [[decode_snapshot_summary()]] - code - django_apps/asteroid_lab/replay/snapshot_map_replay.py
- [[decoded_cell_to_full_map_row()]] - code - django_apps/asteroid_lab/replay/snapshot_map_replay.py
- [[deconstruction_frames.py]] - code - django_apps/asteroid_lab/replay/deconstruction_frames.py
- [[diff_maps()]] - code - django_apps/asteroid_lab/replay/snapshot_map_replay.py
- [[existing_layout_service.py]] - code - django_apps/asteroid_lab/services/existing_layout_service.py
- [[full_map_rows_from_reconstruction()]] - code - django_apps/asteroid_lab/reconstruction/display_map.py
- [[load_cleanup_result()]] - code - django_apps/asteroid_lab/replay/deconstruction_frames.py
- [[merge_reconstruction_display_rows()]] - code - django_apps/asteroid_lab/reconstruction/display_map.py
- [[persist_decoded_cell_snapshot()]] - code - django_apps/asteroid_lab/services/cell_snapshot_service.py
- [[persist_existing_layout_inspection_snapshot()]] - code - django_apps/asteroid_lab/services/existing_layout_service.py
- [[reconstruction_frames.py]] - code - django_apps/asteroid_lab/replay/reconstruction_frames.py
- [[record_decoded_snapshot_frames()]] - code - django_apps/asteroid_lab/services/cell_snapshot_service.py
- [[record_existing_layout_inspection_frames()]] - code - django_apps/asteroid_lab/services/existing_layout_service.py
- [[rows_from_cells()]] - code - django_apps/asteroid_lab/replay/snapshot_map_replay.py
- [[run_reconstruction_for_map_input()]] - code - django_apps/asteroid_lab/services/reconstructed_asteroid_service.py
- [[run_topology_reconstruction()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/pipeline.py
- [[snapshot_map_replay.py]] - code - django_apps/asteroid_lab/replay/snapshot_map_replay.py
- [[snapshot_summary_from_rows()]] - code - django_apps/asteroid_lab/replay/snapshot_map_replay.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/record_existing_layout_inspection_frames
SORT file.name ASC
```

## Connections to other communities
- 14 edges to [[_COMMUNITY_Any]]
- 11 edges to [[_COMMUNITY_DecodedCellDTO]]
- 8 edges to [[_COMMUNITY_reconstruct_after_cleanup()]]
- 7 edges to [[_COMMUNITY_ReconstructionResult]]
- 6 edges to [[_COMMUNITY_deconstruct_snapshot()]]
- 6 edges to [[_COMMUNITY_build_initial_replay_for_map_input()]]
- 5 edges to [[_COMMUNITY_ReplayRecorder]]
- 4 edges to [[_COMMUNITY_build_reconstructed_map_persist_payload(]]
- 2 edges to [[_COMMUNITY_build_reconstruction_complete_map()]]
- 2 edges to [[_COMMUNITY_ReconstructedAsteroidMapAdmin]]
- 2 edges to [[_COMMUNITY_build_decoded_blueprint_snapshot()]]
- 2 edges to [[_COMMUNITY_flowbite.min.js]]
- 1 edge to [[_COMMUNITY_run_full_from_cleanup_recon()]]
- 1 edge to [[_COMMUNITY_AsteroidLabTraceLogger]]
- 1 edge to [[_COMMUNITY_build_normalized_reconstruction_topology]]

## Top bridge nodes
- [[CleanupResult]] - degree 17, connects to 7 communities
- [[DecodedBlueprintSnapshotDTO]] - degree 13, connects to 5 communities
- [[full_map_rows_from_reconstruction()]] - degree 7, connects to 4 communities
- [[build_reconstruction_replay_events()]] - degree 17, connects to 3 communities
- [[record_existing_layout_inspection_frames()]] - degree 17, connects to 3 communities