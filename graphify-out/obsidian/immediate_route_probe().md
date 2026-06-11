---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/shared/route_probe.py"
type: "code"
community: "Coord"
location: "L258"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Coord
---

# immediate_route_probe()

## Connections
- [[BundleCandidate_1]] - `references` [EXTRACTED]
- [[Coord]] - `references` [EXTRACTED]
- [[RouteGoal_1]] - `references` [EXTRACTED]
- [[RouteProbeLimits]] - `references` [EXTRACTED]
- [[RouteProbeResult]] - `calls` [INFERRED]
- [[RouteProbedBundleCandidate]] - `calls` [EXTRACTED]
- [[WeightedTransportRouteDomain_1]] - `calls` [EXTRACTED]
- [[_failed_probe()]] - `calls` [EXTRACTED]
- [[_limits_or_default()]] - `calls` [EXTRACTED]
- [[_reconstruct_path()_1]] - `calls` [EXTRACTED]
- [[bbox_from_coords()]] - `calls` [INFERRED]
- [[neighbors4()]] - `calls` [INFERRED]
- [[route_probe.py_1]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Coord