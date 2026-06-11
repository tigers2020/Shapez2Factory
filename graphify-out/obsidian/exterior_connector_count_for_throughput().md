---
source_file: "django_apps/game_data/services/exterior_transport_capacity.py"
type: "code"
community: "exterior_transport_capacity.py"
location: "L147"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/exterior_transport_capacitypy
---

# exterior_connector_count_for_throughput()

## Connections
- [[Decimal]] - `references` [EXTRACTED]
- [[_external_connector_count()]] - `calls` [INFERRED]
- [[``ceil(max_throughput  per_building_connector_capacity)``; 0 when throughput ≤]] - `rationale_for` [EXTRACTED]
- [[exterior_connector_capacity_per_min()]] - `calls` [EXTRACTED]
- [[exterior_transport_capacity.py_1]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/exterior_transport_capacitypy