# Plan: recipe_graph_builder split (2026-05-02)

Related research: [documents/research_recipe_graph_builder_split_2026-05-02.md](./research_recipe_graph_builder_split_2026-05-02.md)

Original request summary: split graph builder node/edge assembly into smaller helpers while preserving current graph result contract.

## Implementation approach

1. Split usage analysis (`used_output_keys`, `reused_counts`) before `build()` into helper.
2. Extract source shape node creation logic into helper.
3. Extract operation node creation and input edge creation into helpers.
4. Extract output shape node creation and output edge creation into helpers.
5. Keep preview scene serialization as independent helper; builder body calls only.

## Compatibility criteria

- Preserve `RecipeGraphBuilder.build()` public signature.
- Target/source/intermediate role assignment must not change.
- Preserve `Target` / `Target xN` label rules.
- Preserve unused output labels like `Output B (unused)`.
- Preserve `quantity`, `reused_count`, `preview_scene` payload.

## Verification

- `python -m pytest tests/unit/shapez_solver/test_solver_service.py`
- `python -m pytest tests/unit/shapez_solver/test_factory_throughput_service.py`
- `python -m pytest tests/integration/api/test_solver_api.py`
- `python -m mypy django_apps/shapez_solver/services/recipe_graph_builder.py`
- `python -m ruff check django_apps/shapez_solver/services/recipe_graph_builder.py`
