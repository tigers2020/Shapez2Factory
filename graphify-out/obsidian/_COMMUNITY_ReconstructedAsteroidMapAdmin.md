---
type: community
cohesion: 0.19
members: 15
---

# ReconstructedAsteroidMapAdmin

**Cohesion:** 0.19 - loosely connected
**Members:** 15 nodes

## Members
- [[.decoded_json_pretty()_1]] - code - django_apps/asteroid_lab/admin.py
- [[.mini_map_list()_1]] - code - django_apps/asteroid_lab/admin.py
- [[.original_decoded_json_pretty()]] - code - django_apps/asteroid_lab/admin.py
- [[.reconstruction_acceptance()]] - code - django_apps/asteroid_lab/admin.py
- [[.reconstruction_quality_tier()]] - code - django_apps/asteroid_lab/admin.py
- [[Persisted confidence  reconstruction counters (if present).]] - rationale - django_apps/asteroid_lab/reconstruction/display_map.py
- [[ReconstructedAsteroidMap]] - code - django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py
- [[ReconstructedAsteroidMapAdmin]] - code - django_apps/asteroid_lab/admin.py
- [[Reconstruction-complete display map structural cleanup rows merged with recon o]] - rationale - django_apps/asteroid_lab/reconstruction/display_map.py
- [[Topology extent from persist (island-local; PR-F Wave C).]] - rationale - django_apps/asteroid_lab/reconstruction/display_map.py
- [[``_asteroid_lab_reconstruction`` block from persisted ``decoded_json``.]] - rationale - django_apps/asteroid_lab/reconstruction/display_map.py
- [[display_map.py]] - code - django_apps/asteroid_lab/reconstruction/display_map.py
- [[full_map_island_bbox_from_decoded_json()]] - code - django_apps/asteroid_lab/reconstruction/display_map.py
- [[reconstruction_meta_from_decoded_json()]] - code - django_apps/asteroid_lab/reconstruction/display_map.py
- [[reconstruction_summary_from_decoded_json()]] - code - django_apps/asteroid_lab/reconstruction/display_map.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/ReconstructedAsteroidMapAdmin
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_SafeString]]
- 5 edges to [[_COMMUNITY_sync_admin_list_thumbnail()]]
- 3 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_record_existing_layout_inspection_frames]]
- 1 edge to [[_COMMUNITY_admin.py]]
- 1 edge to [[_COMMUNITY_GeneSeed]]

## Top bridge nodes
- [[ReconstructedAsteroidMapAdmin]] - degree 11, connects to 4 communities
- [[ReconstructedAsteroidMap]] - degree 8, connects to 2 communities
- [[display_map.py]] - degree 6, connects to 1 community
- [[reconstruction_summary_from_decoded_json()]] - degree 6, connects to 1 community
- [[reconstruction_meta_from_decoded_json()]] - degree 4, connects to 1 community