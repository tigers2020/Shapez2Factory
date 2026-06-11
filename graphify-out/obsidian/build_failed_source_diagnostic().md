---
source_file: "src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/failed_source_diagnostics.py"
type: "code"
community: "build_failed_source_diagnostic()"
location: "L39"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/build_failed_source_diagnostic
---

# build_failed_source_diagnostic()

## Connections
- [[CommittedRimSeedPlacement]] - `references` [EXTRACTED]
- [[Layer05FailedSourceDiagnostic_1]] - `calls` [EXTRACTED]
- [[Layer05FailureReason]] - `references` [EXTRACTED]
- [[Layer05SourceView_1]] - `references` [EXTRACTED]
- [[RouteGoal_1]] - `references` [EXTRACTED]
- [[_blocked_counts_from_detail()]] - `calls` [EXTRACTED]
- [[_nearest_goal_distance()]] - `calls` [EXTRACTED]
- [[failed_source_diagnostics.py]] - `contains` [EXTRACTED]
- [[failure_reason_to_bucket()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/build_failed_source_diagnostic