---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/candidate_gen.py"
type: "code"
community: "generate_candidates()"
location: "L529"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/generate_candidates
---

# generate_candidates()

## Connections
- [[Deterministic rim candidate pool with immediate route probe (no commit).]] - `rationale_for` [EXTRACTED]
- [[ExteriorConnectionPlan]] - `references` [EXTRACTED]
- [[GeneticSampleSeedSnapshot]] - `references` [EXTRACTED]
- [[Layer03TransportProfile]] - `calls` [EXTRACTED]
- [[ReconstructionCompleteMap]] - `references` [EXTRACTED]
- [[RimAnchor]] - `references` [EXTRACTED]
- [[RimBundleCandidateSet]] - `references` [EXTRACTED]
- [[_ProfileExpansionAccum]] - `calls` [EXTRACTED]
- [[_ProfileExpansionInputs]] - `calls` [EXTRACTED]
- [[bbox_from_coords()]] - `calls` [INFERRED]
- [[build_layer03_observability()]] - `calls` [INFERRED]
- [[build_layer03_transport_profiles()]] - `calls` [INFERRED]
- [[build_rim_bundle_candidate_set()]] - `calls` [INFERRED]
- [[candidate_gen.py]] - `contains` [EXTRACTED]
- [[generate_candidates_for_profile()]] - `calls` [EXTRACTED]
- [[mineable_field_kind_by_coord()]] - `calls` [INFERRED]
- [[run_layer_03_rim_greedy_placement()]] - `calls` [INFERRED]
- [[scan_rim_anchors()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/generate_candidates