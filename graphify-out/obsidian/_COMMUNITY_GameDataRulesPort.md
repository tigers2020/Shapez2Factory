---
type: community
cohesion: 0.11
members: 21
---

# GameDataRulesPort

**Cohesion:** 0.11 - loosely connected
**Members:** 21 nodes

## Members
- [[.__init__()_17]] - code - src/shapez2_factory/application/asteroid_lab/run_stack.py
- [[CapacityResolution]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/capacity.py
- [[Default Asteroid Lab core assembly (no Django).  Concrete adapters are injecte]] - rationale - src/shapez2_factory/bootstrap/asteroid_lab_wiring.py
- [[EVTC capacity resolution for Layer 02.  Decoupled from ``django_apps.game_data]] - rationale - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/capacity.py
- [[Execute the pure decode, reconstruction, stack, and artifact-summary path.]] - rationale - src/shapez2_factory/application/asteroid_lab/run_stack.py
- [[GameDataRulesPort]] - code - src/shapez2_factory/bootstrap/asteroid_lab_wiring.py
- [[Pure Asteroid Lab run-stack use case for the CLI-first artifact path.]] - rationale - src/shapez2_factory/application/asteroid_lab/run_stack.py
- [[RunStackUseCase]] - code - src/shapez2_factory/application/asteroid_lab/run_stack.py
- [[RunStackUseCase_1]] - code - src/shapez2_factory/bootstrap/asteroid_lab_wiring.py
- [[StackRunResult_1]] - code - src/shapez2_factory/application/asteroid_lab/run_stack.py
- [[_capacity_envelope()_1]] - code - src/shapez2_factory/application/asteroid_lab/run_stack.py
- [[_capacity_summary()]] - code - src/shapez2_factory/application/asteroid_lab/run_stack.py
- [[_decimal_str()]] - code - src/shapez2_factory/application/asteroid_lab/run_stack.py
- [[_layer_summary_to_json()]] - code - src/shapez2_factory/application/asteroid_lab/run_stack.py
- [[_stack_result_to_json()]] - code - src/shapez2_factory/application/asteroid_lab/run_stack.py
- [[asteroid_lab_wiring.py]] - code - src/shapez2_factory/bootstrap/asteroid_lab_wiring.py
- [[build_run_stack_use_case()]] - code - src/shapez2_factory/bootstrap/asteroid_lab_wiring.py
- [[capacity.py]] - code - django_apps/asteroid_lab/layers/layer_02_exterior_transport/capacity.py
- [[capacity.py_1]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/capacity.py
- [[resolve_per_connector_capacity()]] - code - src/shapez2_factory/application/asteroid_lab/layers/layer_02_exterior_transport/capacity.py
- [[run_stack.py]] - code - src/shapez2_factory/application/asteroid_lab/run_stack.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/GameDataRulesPort
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_deconstruct_snapshot()]]
- 6 edges to [[_COMMUNITY_Decimal]]
- 4 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_ReconstructionCompleteMap]]
- 2 edges to [[_COMMUNITY_execute_layer_02_exterior_transport_plan]]
- 1 edge to [[_COMMUNITY_build_solver_runtime_replay_frames_from_]]

## Top bridge nodes
- [[GameDataRulesPort]] - degree 11, connects to 4 communities
- [[_capacity_envelope()_1]] - degree 7, connects to 3 communities
- [[_capacity_summary()]] - degree 5, connects to 2 communities
- [[_stack_result_to_json()]] - degree 3, connects to 2 communities
- [[_layer_summary_to_json()]] - degree 3, connects to 2 communities