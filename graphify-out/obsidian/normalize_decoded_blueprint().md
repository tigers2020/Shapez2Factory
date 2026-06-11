---
source_file: "src/shapez2_factory/domain/asteroid_lab/normalization.py"
type: "code"
community: "normalize_decoded_blueprint()"
location: "L16"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/normalize_decoded_blueprint
---

# normalize_decoded_blueprint()

## Connections
- [[.clean()]] - `calls` [INFERRED]
- [[NormalizedBlueprintDTO]] - `calls` [EXTRACTED]
- [[RawDecodedBlueprintDTO]] - `references` [EXTRACTED]
- [[Return a shallow-copied root dict with ``_asteroid_lab_summary`` injected.]] - `rationale_for` [EXTRACTED]
- [[_build_summary()]] - `calls` [EXTRACTED]
- [[build_initial_replay_for_map_input()]] - `calls` [INFERRED]
- [[build_reconstructed_normalized_dto()]] - `calls` [INFERRED]
- [[create_copy_code_map_input()]] - `calls` [INFERRED]
- [[decode_shapez_copy_string()]] - `calls` [INFERRED]
- [[normalization.py_1]] - `contains` [EXTRACTED]
- [[normalize_blueprint_entries()]] - `calls` [INFERRED]
- [[refresh_map_input_from_copy_code()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/normalize_decoded_blueprint