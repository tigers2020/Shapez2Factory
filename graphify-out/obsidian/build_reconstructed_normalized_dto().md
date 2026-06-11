---
source_file: "django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py"
type: "code"
community: "normalize_decoded_blueprint()"
location: "L193"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/normalize_decoded_blueprint
---

# build_reconstructed_normalized_dto()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[DecodedCellDTO]] - `references` [EXTRACTED]
- [[NormalizedBlueprintDTO]] - `calls` [EXTRACTED]
- [[Root with summary + island coord meta (persist ``decoded_json``).]] - `rationale_for` [EXTRACTED]
- [[build_reconstructed_blueprint_root()]] - `calls` [EXTRACTED]
- [[build_reconstructed_map_persist_payload()]] - `calls` [INFERRED]
- [[normalize_decoded_blueprint()]] - `calls` [INFERRED]
- [[reconstruction_blueprint_export.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/normalize_decoded_blueprint