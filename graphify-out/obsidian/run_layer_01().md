---
source_file: "django_apps/asteroid_lab/layers/layer_01_reconstruction/run.py"
type: "code"
community: "build_reconstruction_complete_map()"
location: "L16"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/build_reconstruction_complete_map
---

# run_layer_01()

## Connections
- [[CleanupResult]] - `references` [EXTRACTED]
- [[Layer01ReconstructionOutput]] - `calls` [EXTRACTED]
- [[ReconstructionResult]] - `references` [EXTRACTED]
- [[build_reconstruction_capacity_envelope()]] - `calls` [INFERRED]
- [[build_reconstruction_complete_map()]] - `calls` [INFERRED]
- [[run.py]] - `contains` [EXTRACTED]
- [[run_full_from_cleanup_recon()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/build_reconstruction_complete_map