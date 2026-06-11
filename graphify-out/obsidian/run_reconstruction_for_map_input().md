---
source_file: "django_apps/asteroid_lab/services/reconstructed_asteroid_service.py"
type: "code"
community: "record_existing_layout_inspection_frames"
location: "L32"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/record_existing_layout_inspection_frames
---

# run_reconstruction_for_map_input()

## Connections
- [[CleanupResult]] - `references` [EXTRACTED]
- [[ReconstructionResult]] - `references` [EXTRACTED]
- [[ReconstructionTraceCollector]] - `calls` [EXTRACTED]
- [[Run cleanup + topology reconstruction for one ``AsteroidMapInput``.]] - `rationale_for` [EXTRACTED]
- [[build_decoded_blueprint_snapshot_from_input()]] - `calls` [INFERRED]
- [[load_cleanup_result()]] - `calls` [INFERRED]
- [[reconstructed_asteroid_service.py]] - `contains` [EXTRACTED]
- [[record_existing_layout_inspection_frames()]] - `calls` [INFERRED]
- [[refresh_reconstructed_map_for_map_input()]] - `calls` [EXTRACTED]
- [[run_topology_reconstruction()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/record_existing_layout_inspection_frames