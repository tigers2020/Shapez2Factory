# Solver Graph Generation Logic Research

Date: 2026-05-02

## Scope

- Trace in code how the current solver graph is produced.
- Covers request entry, planner/throughput layer, graph DTO assembly, JSON serialization, and frontend runtime layout.
- Focus is less "what solution is found" and more "how found solutions become graph contract".

## One-Line Summary

The current solver graph is built in this order:

1. `views.py` parses shape codes from the request.
2. `FactoryThroughputService` computes target batch and base demand.
3. `solve_recipe_pipeline()` uses `PlannerService` to produce `SolvedRecipe`.
4. Within the same pipeline, `RecipeGraphBuilder.build()` iterates over `SolvedRecipe.recipes` to build the `SolverGraph` DTO.
5. `serialize_solver_graph()` attaches shape node preview PNG URLs and operation icon URLs and serializes to API JSON.
6. In the browser, `solver_graph_layout.js` computes coordinates from the received `nodes` and `edges`.

The backend builds "graph structure"; the frontend computes "coordinate layout" only.

## 1. Request Entry Point

The entry point is `solve_shape()` in `django_apps/shapez_solver/views.py`.

- Extract `code` from the request.
- Parse it with `parse_shape_code_list()`.
- Use only the first pattern as the target.
- If it differs from the normalized code, accumulate warnings.
- Then call `FactoryThroughputService().solve(...)`.

The graph is not created at this layer. This layer only handles input validation, warning collection, and error response mapping.

## 2. Throughput Stage Prepares Graph Generation

`django_apps/shapez_solver/services/factory_throughput_service.py`

The role of `FactoryThroughputService.solve()` is not to draw the graph directly, but to prepare the quantity context needed by the graph builder.

- When `compute_factory_batch(target_shape)` succeeds, it computes:
  - `target_count`
  - `base_demands`
- For unsupported targets:
  - `target_count = 1`
  - `base_demands = ()`
  - add a warning

It then passes the following values to `solve_recipe_pipeline()`:

- `target_shape`
- `target_count`
- `base_demands`

Thus source quantities, target labels, and target quantity inside the graph are determined at the throughput stage, not by the planner.

## 3. Solve Pipeline: Validate Solution Then Call Graph Builder

`django_apps/shapez_solver/services/solve_pipeline.py`

The `solve_recipe_pipeline()` flow is as follows:

1. `PlannerService.solve_shape(target_shape, SolveContext())`
   - Produces the optimal `SolvedRecipe` for the target.
2. `OperationEngine.evaluate(solved.recipes, solved.ref)`
   - Re-validates that the recipe replay result actually matches the target.
3. If validation passes, `RecipeGraphBuilder.build(...)`
   - Converts `SolvedRecipe` to `SolverGraph`.
4. Separately, `_build_steps(solved)` also builds a step list for the timeline.

The important point at this layer is that the graph builder is separate from the planner.

- Planner responsibility: decide which recipe DAG to select
- Graph builder responsibility: convert the selected recipe DAG into a UI/API contract graph DTO

## 4. Data Structure the Planner Passes to the Graph Builder

`django_apps/shapez_solver/domain/recipe.py`

The graph builder input is `SolvedRecipe`.

- `SolvedRecipe.ref`
  - Pointer indicating which recipe output is the final target
- `SolvedRecipe.recipes`
  - Tuple of `SourceRecipe | OperationRecipe`

Key types:

- `SourceRecipe`
  - Raw material source node candidate
- `OperationRecipe`
  - Processing node candidate such as cutter, rotate, painter, stacker
- `RecipeRef`
  - Indicates which output index of a specific recipe is referenced

The graph builder does not perform separate traversal; it iterates over this `recipes` list to assemble shape nodes, operation nodes, and edges.

## 5. How the Planner Selects `SolvedRecipe`

`django_apps/shapez_solver/services/planner_service.py`

To understand graph shape, you need to know which candidates the planner can produce.

- If it is a direct source, it ends immediately with `try_source()`.
- Otherwise, it tries the following rule candidates in order:
  - rotation
  - stack layers
  - paint
  - assemble halves
  - assemble quadrants
  - cut from source
- Each candidate is validated with `OperationEngine.evaluate(...) == target`.
- Finally, the minimum-cost candidate is adopted via `RecipeCost.as_sort_key()`.

Thus the operation types and branching structure of the graph come from the planner rule set; the graph builder only renders that result.

## 6. Graph DTO Contract

`django_apps/shapez_solver/dto/solver_graph.py`

The graph DTO produced by the backend is simple.

- `SolverGraph`
  - `nodes`
  - `edges`
  - `direction = "left-to-right"`
- `SolverShapeNode`
  - `role`: `source | intermediate | target`
  - `shape_code`, `label`, `preview_scene`, `reused_count`, `quantity`
- `SolverOperationNode`
  - `operation_type`, `label`, `icon`, `input_count`, `output_count`, `description`
- `SolverGraphEdge`
  - `from_id`, `to_id`, `kind`, `slot`, `label`

The important point is that this DTO has no coordinate information. Node positions are computed on the frontend.

## 7. Actual Assembly Order of `RecipeGraphBuilder`

`django_apps/shapez_solver/services/recipe_graph_builder.py`

`RecipeGraphBuilder.build()` operates in the following order:

### 7.1 State Initialization

First, it creates internal state via `_build_state(...)`.

- `nodes`, `edges`
- `seen_shape_nodes`
  - Prevents duplicate addition of the same shape output node
- `final_key`
  - Final target output key
- `used_output_keys`
  - List of outputs actually consumed as operation inputs or that are the final target
- `reused_counts`
  - Reuse count based on how many times the same output is referenced as input
- `target_count`
- `base_quantity_by_shape`
  - Value from converting `base_demands` to a shape code -> quantity map

Here, `final_key` and `used_output_keys` become the basis for target determination and unused output labeling.

### 7.2 Recipe List Iteration

`for recipe in solved.recipes`

- If `SourceRecipe`, call `_append_source_shape_node()`
- If `OperationRecipe`:
  - `_append_operation_node()`
  - `_append_input_edges()`
  - `_append_output_shape_nodes_and_edges()`

Thus a source creates only one shape node, while an operation adds a bundle of "operation node + input edges + output shape nodes + output edges".

## 8. Source Shape Node Creation Rules

`_append_source_shape_node(state, recipe)`

ID rule:

- Source shape node id is always `"{recipe.id}:shape:0"`

Target determination:

- `recipe_key = "{recipe.id}:0"`
- If this equals `state.final_key`, the source is also the final target.

Field rules:

- `role`
  - `target` if final target
  - otherwise `source`
- `label`
  - `Target` or `Target xN` if target
  - otherwise `recipe.label`
- `quantity`
  - `target_count` if target
  - `base_quantity_by_shape.get(shape_code, 1)` if source
- `reused_count`
  - `count - 1` if the same output is referenced multiple times
- `preview_scene`
  - `_serialize_shape_preview(shape)`

So a problem where "source alone becomes target immediately" ends as a single-shape-node graph.

## 9. Operation Node Creation Rules

`_append_operation_node(state, recipe)`

Operation nodes are created by fetching metadata from `OPERATION_CATALOG`.

- `id = recipe.id`
- `operation_type = recipe.operation_type.value`
- `label = recipe.label`
- `icon = operation.icon`
- `input_count`, `output_count`, `description`

Thus operation node display information is the combined result of the recipe object and operation catalog.

## 10. Input Edge Creation Rules

`_append_input_edges(state, recipe)`

One edge is created per input ref.

- `from_id = "{input.recipe_id}:shape:{input.output_index}"`
- `to_id = recipe.id`
- `kind = "input"`
- `slot = label = "Input A"`, `"Input B"` ...

The important point is that input edges go from shape nodes to operation nodes.

## 11. Output Shape Node and Output Edge Creation Rules

`_append_output_shape_nodes_and_edges(state, recipe)`

For each output index:

1. Attempt to add output shape node
2. Add operation -> shape output edge

Output key / id rules:

- `output_key = "{recipe.id}:{output_index}"`
- `output_node_id = "{recipe.id}:shape:{output_index}"`

Shape node field rules:

- `role`
  - `target` if `output_key == final_key`
  - otherwise `intermediate`
- `label`
  - `Target` or `Target xN` if target
  - otherwise `"Shape"`
- `quantity`
  - `target_count` if target
  - `1` if intermediate
- `reused_count`
  - Reflects `_compute_reused_counts()` result
- `preview_scene`
  - `_serialize_shape_preview(output_shape)`

Output edge rules:

- `from_id = recipe.id`
- `to_id = output_node_id`
- `kind = "output"`
- `slot = "Output A"`, `"Output B"` ...
- `label`
  - `"Output A"` if the output is actually used elsewhere or is the final target
  - otherwise `"Output A (unused)"`

The frequently seen `"Output B (unused)"` in tests comes directly from this rule.

## 12. Reused Count Calculation Rules

`_compute_reused_counts(solved)`

Reuse count is based on "how many times the same output is consumed as an operation input".

- Iterate all `OperationRecipe.inputs` and count `"{recipe_id}:{output_index}"`
- Referenced 2 times -> `reused_count = 1`
- Referenced 3 times -> `reused_count = 2`

Thus the displayed value is not total usage count but "additional reuse count excluding the first use".

## 13. Preview Scene Creation Rules

All shape nodes carry `preview_scene`.

- The graph builder pre-populates the scene via `_serialize_shape_preview(shape)`.
- The scene contains `normalized_code` and `cells[]`.
- Each cell includes layer, quadrant, color, mesh/material/transform key.

This scene is used in two places:

1. Exposed as-is in the API payload
2. Input to `GraphPreviewRenderer.render(preview_scene)`

Thus graph node preview is a shape render scene product, not a planner output.

## 14. API JSON Serialization Stage

`django_apps/shapez_solver/view_graph_serialization.py`

`serialize_solver_graph(graph)` converts the `SolverGraph` DTO into the final JSON contract.

- `layout.direction`
  - Currently always `"left-to-right"` from the backend
- `nodes`
  - Serialized separately for shape / operation
- `edges`
  - `from`, `to`, `kind`, `slot`, `label`

Shape node serialization:

- `preview_renderer = get_graph_preview_renderer()`
- `graph_preview = preview_renderer.render(preview_scene)`
- Attaches as result:
  - `preview_scene`
  - `preview_image_url`
  - `preview_alt`

Operation node serialization:

- Generates icon URL via `static("web/images/operations/...")`

Thus the graph builder creates "structure and raw preview scene" up to that point; the serializer completes "URLs the browser can use directly".

## 15. Graph Location in the Final Response Payload

`django_apps/shapez_solver/view_serialization.py`

`serialize_solver_result()` builds the entire solver response and includes:

- `steps`
- `base_demands`
- `warnings`
- `graph`

Here, `graph` is the result of `serialize_solver_graph(result.graph)`.

Thus the graph field in the external API contract is a two-stage conversion result of `FactoryThroughputResult.graph -> SolverGraph -> serialized graph dict`.

## 16. Additional Frontend Work: Layout Calculation

`django_apps/web/static/web/js/solver_graph_layout.js`

The backend passes only node connections; the browser computes actual coordinates.

Key steps:

1. `computeNodeDepths(graph)`
   - Compute DAG depth along edges
2. `groupNodeIdsByDepth(graph, depths)`
   - Group by column per depth
3. `orderNodeIdsByBarycenter(...)`
   - Reorder within column based on predecessor/successor barycenter
4. `computeVerticalTopPositions(...)`
   - Y-position compaction via multiple sweeps
5. `computeHorizontalPositions(...)`
   - Compute X positions considering predecessor positions and same-rank gap
6. `buildFinalGraphLayout(...)`
   - Produce `positions`, `width`, `height`, `bounds`

Thus the current contract is:

- Backend: provides DAG structure and node metadata
- Frontend: computes depth/barycenter-based grouped layout

## 17. Graph Contract Fixed by Tests

The current logic is protected by the following tests:

- `tests/unit/shapez_solver/test_solver_service.py`
  - source-only graph
  - inclusion of rotation / painter / stacker
  - exactly one target node
  - unused output edge labels
  - whether auto batch is reflected in source quantity and target quantity
- `tests/integration/api/test_solver_api.py`
  - API payload `graph.nodes` structure and target quantity / label
- `tests/integration/web/test_web_smoke.py`
  - `layout.direction == "left-to-right"`
  - graph node preview / operation icon contract
  - whether the frontend uses `solver_graph_layout.js`
- `tests/unit/web/test_solver_graph_layout.py`
  - determinism and placement rules of the frontend grouped layout algorithm itself

Thus when refactoring graph-related code, you must not break not only DTO field names but also the following semantic contracts:

- There must be exactly one target node.
- Source quantity may be overridden by base demand.
- Intermediate quantity is currently 1.
- Unused outputs are revealed via edge labels.
- Coordinates are computed by the client, not the server.

## 18. Points to Note When Understanding the Current Structure

1. The planner and graph builder are not the same thing.
   The planner finds the correct recipe; the graph builder converts that result into a visualization DTO.
2. The graph DTO and API JSON are also not the same thing.
   Preview PNG URLs and static icon URLs are attached at the serializer stage.
3. Graph layout is not a backend responsibility.
   The server does not store positions; the frontend computes them based on depth/barycenter.
4. `target_count` strongly affects quantity display across the entire graph.
   In particular, target label and source quantity vary depending on throughput layer calculation results.

## 19. Practical Modification Points

- To change planner rules:
  - `django_apps/shapez_solver/services/planner_service.py`
  - `django_apps/shapez_solver/services/planner_rules.py`
- To change graph node/edge rules:
  - `django_apps/shapez_solver/services/recipe_graph_builder.py`
- To change API graph payload fields:
  - `django_apps/shapez_solver/view_graph_serialization.py`
- To change browser layout only:
  - `django_apps/web/static/web/js/solver_graph_layout.js`

## Conclusion

The core of the current solver graph generation logic is a three-stage conversion centered on `SolvedRecipe`.

1. The planner creates `SolvedRecipe`.
2. `RecipeGraphBuilder` converts it to `SolverGraph`.
3. The serializer and frontend each add "display assets" and "coordinates" respectively.

Thus when debugging graph issues, it is fastest to separate:

- whether the recipe was generated incorrectly
- whether the graph builder mapped incorrectly
- whether the serializer attached preview/icon incorrectly
- whether the frontend layout placed nodes incorrectly
