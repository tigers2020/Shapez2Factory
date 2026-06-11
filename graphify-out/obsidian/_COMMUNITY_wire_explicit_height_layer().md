---
type: community
cohesion: 0.22
members: 15
---

# wire_explicit_height_layer()

**Cohesion:** 0.22 - loosely connected
**Members:** 15 nodes

## Members
- [[Compose replay map_view overlay_cells layers (output-only).]] - rationale - django_apps/asteroid_lab/replay/overlay_composition.py
- [[Merge overlay layers; persistent connector rows must come from plan wire.]] - rationale - django_apps/asteroid_lab/replay/overlay_composition.py
- [[Shapez 2 island height layer (L=012) for replay wire cells.  Golden map copy]] - rationale - django_apps/asteroid_lab/replay/map_height_layer.py
- [[_candidate_dedupe_key()]] - code - django_apps/asteroid_lab/replay/overlay_composition.py
- [[_connector_dedupe_key()]] - code - django_apps/asteroid_lab/replay/overlay_composition.py
- [[_dedupe_rows()]] - code - django_apps/asteroid_lab/replay/overlay_composition.py
- [[_non_connector_structural_rows()]] - code - django_apps/asteroid_lab/replay/overlay_composition.py
- [[_structural_dedupe_key()]] - code - django_apps/asteroid_lab/replay/overlay_composition.py
- [[clamp_replay_height_layer()]] - code - django_apps/asteroid_lab/replay/map_height_layer.py
- [[compose_replay_overlay_cells()]] - code - django_apps/asteroid_lab/replay/overlay_composition.py
- [[enrich_replay_wire_row_with_layer()]] - code - django_apps/asteroid_lab/replay/map_height_layer.py
- [[map_height_layer.py]] - code - django_apps/asteroid_lab/replay/map_height_layer.py
- [[overlay_composition.py]] - code - django_apps/asteroid_lab/replay/overlay_composition.py
- [[resolve_replay_height_layer()]] - code - django_apps/asteroid_lab/replay/map_height_layer.py
- [[wire_explicit_height_layer()]] - code - django_apps/asteroid_lab/replay/map_height_layer.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/wire_explicit_height_layer
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_timeline_serialization.py]]
- 2 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_lab_timeline_adapter.py]]
- 2 edges to [[_COMMUNITY_build_solver_runtime_replay_frames()]]

## Top bridge nodes
- [[wire_explicit_height_layer()]] - degree 9, connects to 3 communities
- [[enrich_replay_wire_row_with_layer()]] - degree 6, connects to 2 communities
- [[compose_replay_overlay_cells()]] - degree 5, connects to 1 community
- [[resolve_replay_height_layer()]] - degree 4, connects to 1 community