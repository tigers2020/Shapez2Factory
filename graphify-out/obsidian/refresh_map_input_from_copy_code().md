---
source_file: "django_apps/asteroid_lab/services/input_service.py"
type: "code"
community: "AsteroidMapInput"
location: "L67"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/AsteroidMapInput
---

# refresh_map_input_from_copy_code()

## Connections
- [[AsteroidMapInput]] - `references` [EXTRACTED]
- [[Overwrite ``copy_code`` and ``decoded_json`` on an existing ``AsteroidMapInput``]] - `rationale_for` [EXTRACTED]
- [[content_sha256_for_copy_code()]] - `calls` [EXTRACTED]
- [[decode_copy_string()]] - `calls` [INFERRED]
- [[input_service.py]] - `contains` [EXTRACTED]
- [[normalize_decoded_blueprint()]] - `calls` [INFERRED]
- [[persist_decoded_snapshot_for_map_input()]] - `calls` [EXTRACTED]
- [[upsert_map_input_for_project()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/AsteroidMapInput