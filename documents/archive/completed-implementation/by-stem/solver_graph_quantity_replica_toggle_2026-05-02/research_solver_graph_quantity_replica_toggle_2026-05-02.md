# solver graph quantity replica toggle research

Date: 2026-05-02

## Request summary

Add a button to the solver graph to make it visible by actually duplicating the base/source and target nodes by `quantity` when turned on.

## Current structure summary

Currently, graph creation and display responsibilities are divided as follows:

- Backend
  - `django_apps/shapez_solver/services/recipe_graph_builder.py`
  - `django_apps/shapez_solver/view_graph_serialization.py`
- Role: Create representative graph structure, node metadata, and preview URL.
- Front
  - `django_apps/web/static/web/js/solver_timeline/timeline_request.js`
  - `django_apps/web/static/web/js/solver_timeline/graph_mount.js`
  - `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
  - `django_apps/web/static/web/js/solver_graph_layout.js`
- Role: Receives a graph, calculates markup and coordinates, and shows selection details.

Important current contracts:

- There is only one source / target node for each recipe output.
- The required quantity is expressed as `quantity`, not the number of nodes.
- The layout is calculated by the client, not the server.

## Observation of related code

### 1. Graph panel entry point

`django_apps/web/templates/web/solver.html`

- The graph panel root is `[data-solver-timeline]`
- Currently there are only target input, error/warning, throughput summary, graph canvas, and detail host.
- It is natural to place the replica toggle UI within this panel.

### 2. graph fetch / mount flow

`django_apps/web/static/web/js/solver_timeline/timeline_request.js`

- Receive the API response and pass it to `mountGraph(panel, graph)`.
- Here, the graph is not saved or separate UI state is not managed.

`django_apps/web/static/web/js/solver_timeline/graph_mount.js`

- Render HTML with `renderSolverGraph(graph)`
- Connect click selection event and detail panel render
- The default selection is `role === "target"` node priority.

In other words, in order to reflect the toggle state, `mountGraph()` must be able to handle the original graph and the derived graph separately.

### 3. Graph markup / coordinate calculation

`django_apps/web/static/web/js/solver_timeline/graph_markup.js`

- `renderSolverGraph(graph)` directly calls `computeGraphLayout(graph)`.
- node id is the standard for DOM `data-graph-node-id` and selection status.
- The quantity badge is for labeling, not cloning the current node.

`django_apps/web/static/web/js/solver_graph_layout.js`

- Calculate the DAG layout by purely receiving the given `nodes` and `edges`.
- In other words, replica toggle can be solved by deriving and creating the input graph without changing the layout algorithm.

### 4. Select Detail Panel

`django_apps/web/static/web/js/solver_timeline/graph_detail.js`

- Find a node directly in `graph.nodes` with the selected node id.
- Connection edges are also calculated from the same graph object.

So, if you create a clone node:

- The replica node id must not conflict with the original.
- The detail panel must be able to normally view replica nodes.

## Safest implementation direction

The safest method is to maintain the backend payload and create a “derived graph for replication display” at the front.

reason:

1. No need to touch the current API/serializer/DTO contract.
2. The existing solver graph creation logic and testing can be maintained almost as is.
3. Since toggle is a pure UI state, it is more natural to place it at the front.

## Draft derived graph creation rules

If toggle is off, the current graph is used as is.

If toggle is on:

- a node with `role === "source"` and `quantity > 1`:
- Create replica nodes according to the quantity
- A node with `role === "target"` and `quantity > 1`:
- Create replica nodes according to the quantity
- Other intermediate / operation nodes:
- Remain original

Replication rule candidates:

### source node

- Remove the original source node and replace it with replicas.
- Each replica quantity is `1`
- Each replica is connected to the same operation edge destination as the original source.

yes:

- Source: `source SuSuSuSu quantity=2`
- Conversion:
  - `source SuSuSuSu #1 quantity=1`
  - `source SuSuSuSu #2 quantity=1`
- Both replicas are edge connected to the same downstream operation

### target node

- Remove the original target node and replace it with replicas.
- Each replica quantity is `1`
- Replicate the upstream output edge from the original target to all replicas

yes:

- Original: `target CuRuSuSu quantity=4`
- Conversion:
  - `target #1`
  - `target #2`
  - `target #3`
  - `target #4`
- Upstream operation output edge is replicated to each target replica

## Open decision points

### 1. Whether to maintain the toggle display even when the target/source quantity is 1.

suggestion:

- The button is always visible, but the actual node number change only occurs when `quantity > 1`.

reason:

- Good UI consistency.
- Users can understand the existence of functions even if there is no change in some shapes.

### 2. How the replica label will look

Candidate:

- `Source #1`, `Source #2`
- `Target #1`, `Target #2`
- Leave the shape code as is and only add the badge to `COPY 1/4`

suggestion:

- Maintain the existing `label` and display `COPY 1/4` or `COPY 2/4` with a small badge.

reason:

-Does not harm the original meaning.
- Detail panels and card text are less loud.

### 3. Detail panel quantity indication

Since a duplicate node represents one real object, `Quantity x1` is natural for detail.

Instead, if you need the original context, add replica metadata:

- `Replica 2 of 4`
- `Expanded from target quantity`

It may seem like that.

## Tests Impact

### integration web

`tests/integration/web/test_web_smoke.py`

- Need to check if the toggle button marker is rendered on the solver page
- Existing smoke markers must be kept unbroken.

### unit web

Looks like a new test is needed.

Candidate:

- Pure unit testing of helpers like `expandGraphQuantities()`
- source quantity 2 -> 2 source nodes
- target quantity 4 -> 4 target nodes
- Maintain intermediate/operation node
- Check the number of edge replications
- Check the immutability of the existing original graph
- layout testing
- Does the extended graph also satisfy the left-to-right edge condition in `computeGraphLayout()`?

## Risk

1. As the number of target replicas increases, the fan-out edge greatly increases in the same upstream operation.
2. If there are many source replicas, edges may appear overlapping in the same downstream operation.
3. The default selection value is “first target”, but if there are multiple target replicas, you must decide which replica to select as default.
4. If the meaning of replica in the detail panel is ambiguous, users may wonder, “Why are there multiple nodes that are all the same?”

## conclusion

The safest way to use this feature is to create a toggle-based derived graph on the front rather than changing the backend graph contract.

The core scope of work is:

- Add toggle button to solver page
- Add UI state to graph mount path
- Add front helper to expand source/target quantity to replica nodes
- Reinforcement of replica cards and detail UI
- Add unit/integration test
