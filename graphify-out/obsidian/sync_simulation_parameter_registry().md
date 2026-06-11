---
source_file: "django_apps/game_data/services/simulation_parameter_registry.py"
type: "code"
community: "import_simulation_systems()"
location: "L53"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/import_simulation_systems
---

# sync_simulation_parameter_registry()

## Connections
- [[Any]] - `references` [EXTRACTED]
- [[Record top-level keys for one system; drop stale occurrences. Returns key names]] - `rationale_for` [EXTRACTED]
- [[SimulationSystem]] - `references` [EXTRACTED]
- [[_ensure_parameter_key()]] - `calls` [EXTRACTED]
- [[_source_path_for_key()]] - `calls` [EXTRACTED]
- [[import_simulation_systems()]] - `calls` [INFERRED]
- [[simulation_parameter_registry.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/import_simulation_systems