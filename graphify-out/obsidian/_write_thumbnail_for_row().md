---
source_file: "django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py"
type: "code"
community: "sync_admin_list_thumbnail()"
location: "L66"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/sync_admin_list_thumbnail
---

# _write_thumbnail_for_row()

## Connections
- [[ReconstructedAsteroidMap]] - `references` [EXTRACTED]
- [[_persist_thumbnail_metadata()]] - `calls` [EXTRACTED]
- [[clear_admin_list_thumbnail()]] - `calls` [EXTRACTED]
- [[compute_list_thumbnail_window()]] - `calls` [INFERRED]
- [[reconstructed_map_thumbnail_service.py]] - `contains` [EXTRACTED]
- [[render_list_thumbnail_image_bytes()]] - `calls` [INFERRED]
- [[sync_admin_list_thumbnail()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/sync_admin_list_thumbnail