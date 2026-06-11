---
source_file: "django_apps/asteroid_lab/services/input_service.py"
type: "code"
community: "AsteroidMapInput"
location: "L87"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/AsteroidMapInput
---

# upsert_map_input_for_project()

## Connections
- [[AsteroidMapInput]] - `references` [EXTRACTED]
- [[AsteroidProject_1]] - `references` [EXTRACTED]
- [[Create or overwrite the map input row for this copy digest (``created`` flag).]] - `rationale_for` [EXTRACTED]
- [[asteroid_miner_layout_create_project()]] - `calls` [INFERRED]
- [[content_sha256_for_copy_code()]] - `calls` [EXTRACTED]
- [[create_copy_code_map_input()]] - `calls` [EXTRACTED]
- [[create_project_from_copy_code()]] - `calls` [INFERRED]
- [[input_service.py]] - `contains` [EXTRACTED]
- [[refresh_map_input_from_copy_code()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/AsteroidMapInput