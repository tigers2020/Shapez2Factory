# solver bundle overlay research
Date: 2026-05-03

## Scope

- Before designing `bundle_overlay`, which bundles specific patterns into semantic units, we checked the current solver graph creation and rendering boundaries.
- The target macro phases are `quad_stage`, `checker_stage`, and `swap_stage`.
- This document is the result of an investigation before changing the code, and is premised on not changing the meaning of atomic graph and materialized graph.

## Current Graph Contract

- The graph DTO is centered on `SolverGraph`, `SolverShapeNode`, `SolverOperationNode`, and `SolverGraphEdge` in `django_apps/shapez_solver/dto/solver_graph.py`.
- The shape node has `role`, `shape_code`, `quantity`, `produced_state`, and batch metadata.
- The operation node has `operation_type`, port count, icon, and run metadata.
- An edge has only `from_id`, `to_id`, `kind`, `slot`, and `label`.
- `SolverGraph.group_annotation` is an optional field and is currently serialized as `groups` in graph JSON.

## Materialized Graph

- `MaterializedGraphBuilder` unfolds the actual production flow by the node/edge quantity by reflecting the target count and base demands.
- The materialized graph does not express target/source quantity only as a single number, but also includes batch item, operation run, and unused output.
- Therefore, if you actually merge nodes in the materialized graph, the quantity, batch, unused output, and target output count may be broken.
- The current builder attaches an operation-oriented group annotation using `_with_group_annotation()` after creating the graph.

## Existing Group Annotation

- `group_annotation_builder.py` groups input, output, and boundary ref around one operation.
- The main purpose of `groups` is to reliably place the operation card and its surrounding shape cards as background boxes in the front layout.
- `groups.node_ownership` is close to projection that assigns one node to one group.
- This structure is suitable for operation run group, but not for macro covers with overlapping semantic units such as `checker_stage` and `swap_stage`.

## Serialization And Frontend

- `view_graph_serialization.py` exports `nodes`, `edges`, `layout`, and optionally `groups`.
- The front graph renderer reads `groups` from `solver_timeline/graph_markup.js` and `solver_graph_layout.js` and draws group background and boundary ref indicators.
- The detail panel directly searches the original `graph.nodes` and `graph.edges` with the selected node ID.
- Therefore, even if you create a bundle collapsed UI, the original graph is preserved, and a UI-specific derived graph or overlay rendering path is required.

## Why Bundle Must Be Overlay

- `quad_stage`, `checker_stage`, and `swap_stage` are not one general operation, but semantic units that penetrate multiple operations and shapes.
- The same node can belong to the lower preparation stage and the upper macro stage at the same time.
- In the strict partition method, an ownership conflict occurs the moment checker output is used as swap input.
- The bundle must be a cover, not a partition, and internal data must allow overlap.
- You only need to select `visible_bundle_id` in UI collapse.

## Proposed Separation

| Structure | Responsibility | Overlap |
| --- | --- | --- |
| `nodes` / `edges` | source of truth in calculations and quantities | Not applicable |
| `groups` | operation-centered layout auxiliary projection | By default, single ownership |
| `bundle_overlay` | quad/checker/swap Meaning Unit macro cover | allow |

## Detection Inputs

Information that can be used directly by the detector based on the current DTO:

- operation node: `operation_type`
- shape node: `shape_code`, `role`, `produced_state`
- Graph topology: input/output edge direction

Additional helpers required in the initial implementation:

- Incoming/outgoing edge index by node ID
- Inference of operation input shape and output shape
- quad-ready/checker/permutation judgment function based on `shape_code` parser

## Risks

- If the existing `groups` key is reused for bundle purposes, the layout group and macro bundle meanings are mixed.
- Physically reducing the materialized graph corrupts the batch and unused output representations.
- If the detector only searches from the front, false positives may increase in patterns with clearer result shapes, such as checkers.
- If you limit the swap decision to only `operation_type == "swapper"`, you may miss the shape permutation-based swap-like macro.

## Conclusion

- For subsequent implementations, it is safest to leave the existing `groups` as is and add a new `bundle_overlay`.
- Bundle detection is performed as a separate pass after creating the materialized graph.
- The original graph is not changed and only bundle id, macro type, member node ids, boundary edge refs, and visible assignment are sent as annotations.
