---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py"
type: "code"
community: "Coord"
location: "L138"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Coord
---

# weighted_route_probe()

## Connections
- [[BundleCandidate_1]] - `references` [EXTRACTED]
- [[Coord]] - `references` [EXTRACTED]
- [[RouteGoal_1]] - `references` [EXTRACTED]
- [[RouteProbeLimits]] - `references` [EXTRACTED]
- [[RouteProbeResult]] - `calls` [INFERRED]
- [[RouteProbedBundleCandidate]] - `calls` [EXTRACTED]
- [[WeightedTransportRouteDomain_1]] - `references` [EXTRACTED]
- [[_failed_probe()]] - `calls` [EXTRACTED]
- [[_field_cells_on_path()]] - `calls` [EXTRACTED]
- [[_limits_or_default()]] - `calls` [EXTRACTED]
- [[_reconstruct_path()_1]] - `calls` [EXTRACTED]
- [[_resolve_external_void_cells()]] - `calls` [EXTRACTED]
- [[generate_candidates_for_profile()]] - `calls` [INFERRED]
- [[neighbors4()]] - `calls` [INFERRED]
- [[route_probe.py_1]] - `contains` [EXTRACTED]
- [[try_commit_reprobe()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Coord