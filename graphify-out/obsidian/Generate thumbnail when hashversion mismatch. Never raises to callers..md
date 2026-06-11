---
source_file: "django_apps/asteroid_lab/services/reconstructed_map_thumbnail_service.py"
type: "rationale"
community: "sync_admin_list_thumbnail()"
location: "L91"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/sync_admin_list_thumbnail
---

# Generate thumbnail when hash/version mismatch. Never raises to callers.

## Connections
- [[sync_admin_list_thumbnail()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/sync_admin_list_thumbnail