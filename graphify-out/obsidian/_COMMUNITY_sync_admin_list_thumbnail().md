---
type: community
cohesion: 0.14
members: 21
---

# sync_admin_list_thumbnail()

**Cohesion:** 0.14 - loosely connected
**Members:** 21 nodes

## Members
- [[.clear_admin_list_thumbnails()]] - code - django_apps/asteroid_lab/admin.py
- [[.regenerate_admin_list_thumbnails()]] - code - django_apps/asteroid_lab/admin.py
- [[.save_model()]] - code - django_apps/asteroid_lab/admin.py
- [[Admin changelist thumbnails for ReconstructedAsteroidMap (display-only).]] - rationale - django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py
- [[BaseException]] - code - django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py
- [[Generate thumbnail when hashversion mismatch. Never raises to callers.]] - rationale - django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py
- [[ListThumbnailWindow]] - code - django_apps/asteroid_lab/admin_map_list_thumbnail.py
- [[ListThumbnailWindow_1]] - code - django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py
- [[Raster admin changelist thumbnails for reconstructed maps (display-only).]] - rationale - django_apps/asteroid_lab/admin_map_list_thumbnail.py
- [[Return (image_bytes, extension) where extension is webp or png.]] - rationale - django_apps/asteroid_lab/admin_map_list_thumbnail.py
- [[_fill_for_cell()]] - code - django_apps/asteroid_lab/admin_map_list_thumbnail.py
- [[_persist_thumbnail_metadata()]] - code - django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py
- [[_thumbnail_error_types()]] - code - django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py
- [[_write_thumbnail_for_row()]] - code - django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py
- [[admin_map_list_thumbnail.py]] - code - django_apps/asteroid_lab/admin_map_list_thumbnail.py
- [[canonical_decoded_json_hash()]] - code - django_apps/asteroid_lab/admin_map_list_thumbnail.py
- [[clear_admin_list_thumbnail()]] - code - django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py
- [[compute_list_thumbnail_window()]] - code - django_apps/asteroid_lab/admin_map_list_thumbnail.py
- [[reconstructed_map_thumbnail_service.py]] - code - django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py
- [[render_list_thumbnail_image_bytes()]] - code - django_apps/asteroid_lab/admin_map_list_thumbnail.py
- [[sync_admin_list_thumbnail()]] - code - django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/sync_admin_list_thumbnail
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_ReconstructedAsteroidMapAdmin]]
- 3 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_build_decoded_blueprint_snapshot()]]
- 1 edge to [[_COMMUNITY_DecodedCellDTO]]
- 1 edge to [[_COMMUNITY_Command]]
- 1 edge to [[_COMMUNITY_build_reconstructed_map_persist_payload(]]

## Top bridge nodes
- [[sync_admin_list_thumbnail()]] - degree 11, connects to 3 communities
- [[render_list_thumbnail_image_bytes()]] - degree 7, connects to 2 communities
- [[compute_list_thumbnail_window()]] - degree 6, connects to 2 communities
- [[_write_thumbnail_for_row()]] - degree 7, connects to 1 community
- [[canonical_decoded_json_hash()]] - degree 3, connects to 1 community