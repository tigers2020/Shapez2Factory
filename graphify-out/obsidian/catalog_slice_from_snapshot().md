---
source_file: "src/shapez2_factory/domain/asteroid_lab/building_catalog_slice.py"
type: "code"
community: "catalog_slice_from_snapshot()"
location: "L40"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/catalog_slice_from_snapshot
---

# catalog_slice_from_snapshot()

## Connections
- [[AsteroidGameDataSnapshot]] - `references` [EXTRACTED]
- [[BuildingCatalogSlice]] - `calls` [EXTRACTED]
- [[Extract identity, transport registry, and per-variant geometry for the allowlist]] - `rationale_for` [EXTRACTED]
- [[VariantGeometryCatalog]] - `calls` [EXTRACTED]
- [[VariantIdentity]] - `calls` [EXTRACTED]
- [[build_asteroid_game_data_snapshot_with_provenance()]] - `calls` [INFERRED]
- [[building_catalog_slice.py_1]] - `contains` [EXTRACTED]
- [[validate_building_snapshot()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/catalog_slice_from_snapshot