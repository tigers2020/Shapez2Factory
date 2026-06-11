---
source_file: "django_apps/web/services/asteroid_game_data_snapshot.py"
type: "code"
community: "build_asteroid_game_data_snapshot_with_p"
location: "L108"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/build_asteroid_game_data_snapshot_with_p
---

# build_asteroid_game_data_snapshot_with_provenance()

## Connections
- [[GameDataSnapshotBuildResult]] - `calls` [EXTRACTED]
- [[Pin latest import batch once; return snapshot + provenance (sole construction si]] - `rationale_for` [EXTRACTED]
- [[_build_asteroid_game_data_snapshot_for_batch()]] - `calls` [EXTRACTED]
- [[_run_solver_post_traced()]] - `calls` [INFERRED]
- [[asteroid_game_data_snapshot.py]] - `contains` [EXTRACTED]
- [[build_asteroid_game_data_snapshot()]] - `calls` [EXTRACTED]
- [[catalog_slice_from_snapshot()]] - `calls` [INFERRED]
- [[pin_latest_import_batch()]] - `calls` [INFERRED]
- [[provenance_from_snapshot()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/build_asteroid_game_data_snapshot_with_p