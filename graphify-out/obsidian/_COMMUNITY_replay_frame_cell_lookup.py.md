---
type: community
cohesion: 0.23
members: 16
---

# replay_frame_cell_lookup.py

**Cohesion:** 0.23 - loosely connected
**Members:** 16 nodes

## Members
- [[Island-local minmax xy from replay frame bbox (PR-F preferred).]] - rationale - django_apps/web/services/replay_frame_cell_lookup.py
- [[Lab UI only slot inside frame bbox with no persisted row (not solver input).]] - rationale - django_apps/web/services/replay_frame_cell_lookup.py
- [[Paint order full_map + diff; else overlay; else bbox-empty synthetic cell.]] - rationale - django_apps/web/services/replay_frame_cell_lookup.py
- [[Resolve one (x, y) cell payload from a serialized lab replay frame (read-only).]] - rationale - django_apps/web/services/replay_frame_cell_lookup.py
- [[_append_cells()]] - code - django_apps/web/services/replay_frame_cell_lookup.py
- [[_bbox_blocks()]] - code - django_apps/web/services/replay_frame_cell_lookup.py
- [[_cells_at_xy()]] - code - django_apps/web/services/replay_frame_cell_lookup.py
- [[_collect_overlay_cells()]] - code - django_apps/web/services/replay_frame_cell_lookup.py
- [[_island_bbox_from_serialized()]] - code - django_apps/web/services/replay_frame_cell_lookup.py
- [[_lab_empty_synthetic_cell()]] - code - django_apps/web/services/replay_frame_cell_lookup.py
- [[_merge_layers()]] - code - django_apps/web/services/replay_frame_cell_lookup.py
- [[_push_from_blocks()]] - code - django_apps/web/services/replay_frame_cell_lookup.py
- [[_try_synthetic_lab_empty()]] - code - django_apps/web/services/replay_frame_cell_lookup.py
- [[_xy_match()]] - code - django_apps/web/services/replay_frame_cell_lookup.py
- [[lookup_cell_in_serialized_frame()]] - code - django_apps/web/services/replay_frame_cell_lookup.py
- [[replay_frame_cell_lookup.py]] - code - django_apps/web/services/replay_frame_cell_lookup.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/replay_frame_cell_lookuppy
SORT file.name ASC
```

## Connections to other communities
- 11 edges to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY__run_solver_post_traced()]]

## Top bridge nodes
- [[lookup_cell_in_serialized_frame()]] - degree 9, connects to 2 communities
- [[_try_synthetic_lab_empty()]] - degree 6, connects to 1 community
- [[_collect_overlay_cells()]] - degree 5, connects to 1 community
- [[_island_bbox_from_serialized()]] - degree 5, connects to 1 community
- [[_xy_match()]] - degree 4, connects to 1 community