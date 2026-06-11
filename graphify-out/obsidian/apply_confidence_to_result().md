---
source_file: "src/shapez2_factory/domain/asteroid_lab/reconstruction/confidence.py"
type: "code"
community: "ReconstructionResult"
location: "L171"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/ReconstructionResult
---

# apply_confidence_to_result()

## Connections
- [[Attach confidence fields and summary metrics to a reconstruction result.]] - `rationale_for` [EXTRACTED]
- [[CleanupResult]] - `references` [EXTRACTED]
- [[Coord]] - `references` [EXTRACTED]
- [[ReconstructionResult]] - `calls` [EXTRACTED]
- [[_constraint_violations()]] - `calls` [EXTRACTED]
- [[_finalize_reconstruction_result()]] - `calls` [INFERRED]
- [[_is_hard_evidence_cell()]] - `calls` [EXTRACTED]
- [[_topology_coord()]] - `calls` [EXTRACTED]
- [[acceptance_topology_from_reconstruction()]] - `calls` [INFERRED]
- [[build_candidate_masks()]] - `calls` [EXTRACTED]
- [[build_reconstruction_complete_map()]] - `calls` [INFERRED]
- [[compute_confidence_metrics()]] - `calls` [EXTRACTED]
- [[confidence.py_1]] - `contains` [EXTRACTED]
- [[merge_mask_agreement()]] - `calls` [EXTRACTED]
- [[quality_tier_from_metrics()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/ReconstructionResult