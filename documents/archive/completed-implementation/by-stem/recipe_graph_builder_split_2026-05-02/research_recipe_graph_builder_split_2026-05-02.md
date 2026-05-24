# recipe_graph_builder split research (2026-05-02)

- Target file: [django_apps/shapez_solver/services/recipe_graph_builder.py](../../../../../django_apps/shapez_solver/services/recipe_graph_builder.py).
- Four responsibility groups:
  1. recipe graph orchestration (`RecipeGraphBuilder.build`)
  2. source/operation/output node draft assembly
  3. input/output edge assembly
  4. shape preview scene serialization
- External caller today is only `RecipeGraphBuilder().build()` in [solve_pipeline.py](../../../../../django_apps/shapez_solver/services/solve_pipeline.py).
- Tests do not call `RecipeGraphBuilder` directly but [tests/unit/shapez_solver/test_solver_service.py](../../../../../tests/unit/shapez_solver/test_solver_service.py), [tests/unit/shapez_solver/test_factory_throughput_service.py](../../../../../tests/unit/shapez_solver/test_factory_throughput_service.py), [tests/integration/api/test_solver_api.py](../../../../../tests/integration/api/test_solver_api.py) verify graph node role, label, quantity, unused output edge contracts.
- Largest cohesion issue in `build()`: source node, operation node, output shape node, and edge creation mixed in one loop.
- `base_demands` argument is currently ignored via `del base_demands`; looks like future extension hook — keep for signature compatibility.
- Safe split: keep public class name; internal helpers:
  1. recipe usage analysis (`used_output_keys`, `reused_counts`)
  2. source node append helper
  3. operation node append helper
  4. output shape node append helper
  5. preview serialization helper
- Leaves `RecipeGraphBuilder.build()` as loop orchestration only; reduces read/edit cost without changing rules.
