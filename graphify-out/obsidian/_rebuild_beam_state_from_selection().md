---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/beam_selector.py"
type: "code"
community: "RouteProbedBundleCandidate"
location: "L223"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/RouteProbedBundleCandidate
---

# _rebuild_beam_state_from_selection()

## Connections
- [[BeamPenaltyWeights_1]] - `references` [EXTRACTED]
- [[CommitDomainState]] - `calls` [EXTRACTED]
- [[CommitReprobeContext]] - `references` [EXTRACTED]
- [[Coord]] - `references` [EXTRACTED]
- [[RouteProbedBundleCandidate]] - `references` [EXTRACTED]
- [[_BeamState]] - `calls` [EXTRACTED]
- [[_apply_fill_pass_to_result()]] - `calls` [EXTRACTED]
- [[_corridor_cells()]] - `calls` [EXTRACTED]
- [[_equipment_cells()]] - `calls` [EXTRACTED]
- [[_extend()]] - `calls` [EXTRACTED]
- [[_respects_rim_platform()]] - `calls` [EXTRACTED]
- [[beam_selector.py]] - `contains` [EXTRACTED]
- [[try_commit_reprobe()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/RouteProbedBundleCandidate