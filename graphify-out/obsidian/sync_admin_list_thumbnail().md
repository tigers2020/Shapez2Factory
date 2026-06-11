---
source_file: "django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py"
type: "code"
community: "sync_admin_list_thumbnail()"
location: "L86"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/sync_admin_list_thumbnail
---

# sync_admin_list_thumbnail()

## Connections
- [[.handle()]] - `calls` [INFERRED]
- [[.regenerate_admin_list_thumbnails()]] - `calls` [INFERRED]
- [[.save_model()]] - `calls` [INFERRED]
- [[Generate thumbnail when hashversion mismatch. Never raises to callers.]] - `rationale_for` [EXTRACTED]
- [[ReconstructedAsteroidMap]] - `references` [EXTRACTED]
- [[_thumbnail_error_types()]] - `calls` [EXTRACTED]
- [[_write_thumbnail_for_row()]] - `calls` [EXTRACTED]
- [[canonical_decoded_json_hash()]] - `calls` [INFERRED]
- [[clear_admin_list_thumbnail()]] - `calls` [EXTRACTED]
- [[persist_reconstructed_asteroid_map()]] - `calls` [INFERRED]
- [[reconstructed_map_thumbnail_service.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/sync_admin_list_thumbnail