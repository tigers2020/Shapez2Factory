---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/contracts/route_probe_diagnostic.py"
type: "code"
community: "Coord"
location: "L109"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Coord
---

# classify_exterior_goal_unreachable()

## Connections
- [[CandidateRejectReason_1]] - `references` [EXTRACTED]
- [[Coord]] - `references` [EXTRACTED]
- [[Map a failed probe to a detailed reject reason + diagnostic payload.]] - `rationale_for` [EXTRACTED]
- [[RouteGoal_1]] - `references` [EXTRACTED]
- [[RouteProbeDiagnostic]] - `calls` [EXTRACTED]
- [[TransportKind]] - `references` [EXTRACTED]
- [[_failed_probe()]] - `calls` [INFERRED]
- [[_manhattan()]] - `calls` [EXTRACTED]
- [[_stub_void_coord()]] - `calls` [EXTRACTED]
- [[_unweighted_walkable_bfs()]] - `calls` [EXTRACTED]
- [[label_void_components()]] - `calls` [EXTRACTED]
- [[route_probe_diagnostic.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Coord