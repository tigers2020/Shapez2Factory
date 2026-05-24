# Plan: solver bundle overlay
Date: 2026-05-03

Related research: [research_solver_bundle_overlay_2026-05-03.md](./research_solver_bundle_overlay_2026-05-03.md)

## Goal

- Atomic nodes/edges of the materialized graph are preserved as is.
- `quad_stage`, `checker_stage`, and `swap_stage` are expressed as separate `bundle_overlay` annotations.
- The existing `groups` are maintained as an operation-oriented layout projection, and the bundle is separated into a semantic unit macro cover.

## Data Model

A new DTO module was added in a subsequent implementation.

```python
@dataclass(frozen=True, slots=True)
class GraphBundle:
"""A bundle of semantic unit macros to be displayed on the solver graph."""

    id: str
    macro_type: str
    label: str
    member_node_ids: frozenset[str]
    input_boundary_edge_ids: tuple[str, ...]
    output_boundary_edge_ids: tuple[str, ...]
    anchor_node_id: str
    depth: int
    score: float


@dataclass(frozen=True, slots=True)
class BundleOverlay:
"""Bundle annotation result that does not change the original graph."""

    bundles: tuple[GraphBundle, ...]
    node_to_bundle_ids: dict[str, frozenset[str]]
    visible_node_to_bundle_id: dict[str, str]
```

- Since the edge currently does not have an id, the serializer creates a stable edge ref in the form of `"{from_id}->{to_id}:{kind}:{slot}"` or receives separate approval whether to add `SolverGraphEdge.id` in subsequent implementations.
- The default value in this implementation uses a stable edge ref inside the serializer/helper to reduce DTO signature changes.

## Detection Pipeline

After `MaterializedGraphBuilder` and `RecipeGraphBuilder` create a graph, the next pass is added.

```text
SolverGraph
  -> build_group_annotation()
  -> build_bundle_overlay()
  -> serialize_solver_graph()
```

Implementation candidates:

- `BundlePatternDetector` protocol: `macro_type`, `detect(graph) -> list[GraphBundle]`
- `QuadStageDetector`: Starting from source/base, it follows the cut, rotate, stacker, and painter series to group quad-ready shapes.
- `CheckerStageDetector`: Collect backwards from the anchor operation that creates the checker output shape.
- `SwapStageDetector`: Collects `operation_type == "swapper"` or permutation-only output backwards as an anchor.

Early detectors operate conservatively.

- Only bundles that can be clearly determined are created.
- Undeterminable shapes do not create bundles.
- Mark the checker heuristic advancement point with a TODO comment.

## Resolver Rules

- A bundle is a cover, not a partition. One node can belong to multiple bundles.
- All memberships are preserved in `node_to_bundle_ids`.
- The representative bundle for UI collapse is selected by the resolver.

Priority:

```text
swap_stage > checker_stage > quad_stage
```

selection key:

```python
(macroPriority[macro_type], score, len(member_node_ids))
```

If there is a tie, `bundle.id` is fixed in alphabetical order to ensure deterministic output.

## JSON Contract

Existing `nodes`, `edges`, and `groups` do not change.

```json
{
  "nodes": [
    {
      "id": "materialized:swapper:run:1",
      "kind": "operation",
      "operation": {"type": "swapper"},
      "bundle_ids": ["bundle_checker_x", "bundle_swap_y"],
      "visible_bundle_id": "bundle_swap_y"
    }
  ],
  "bundle_overlay": {
    "bundles": [
      {
        "id": "bundle_swap_y",
        "macro_type": "swap_stage",
        "label": "Swap",
        "member_node_ids": ["shape:a", "materialized:swapper:run:1", "shape:b"],
        "input_boundary_edge_ids": ["shape:a->materialized:swapper:run:1:input:Input A"],
        "output_boundary_edge_ids": ["materialized:swapper:run:1->shape:b:output:Output A"],
        "anchor_node_id": "materialized:swapper:run:1",
        "depth": 0,
        "score": 1.0
      }
    ],
    "node_to_bundle_ids": {
      "materialized:swapper:run:1": ["bundle_checker_x", "bundle_swap_y"]
    },
    "visible_node_to_bundle_id": {
      "materialized:swapper:run:1": "bundle_swap_y"
    }
  }
}
```

## UI Follow-up

Phase 1 only provides JSON overlay.

Create a collapsed graph in Phase 2.

- Create a super-node for each bundle ID.
- Hide the edges inside the bundle.
- Only the boundary edge is exposed to the outside.
- The click/detail panel shows bundle summary and member atomic nodes.
- In expanded mode, the existing atomic graph renderer is used as is.

## Test Plan

- DTO unit test: create `GraphBundle`, `BundleOverlay` and check immutability
- detector synthetic graph test:
  - source -> cutter -> rotate -> stacker -> quad-ready shape
  - two branches -> stacker/checker output
  - checker output -> swapper -> target
- resolver test:
- Select `swap_stage` when the same node all belongs to quad/checker/swap
- Check score and member count tie-break deterministic
- serializer/API testing:
- Existing `groups` are maintained.
- A new `bundle_overlay` is added.
- The node payload includes `bundle_ids` and `visible_bundle_id`.
- UI follow-up testing:
- Only super-nodes and boundary edges are rendered in collapsed mode
- Atomic nodes/edges are preserved in expanded mode

## Validation Commands

After subsequent implementation is done, Rex verifies it in the following order.

```text
pytest
ruff check .
mypy .
black .
```

In CI, use `black --check .` with no file changes.

## Migration

- Since there is no DB model change, migration is not necessary.
- Expected changes are limited to DTO, service pass, serializer, and frontend renderer/test.

## CURSOR_MEMO Update

- Since `documents/CURSOR_MEMO.md` exists, this decision was added briefly.
- Record contents are limited to “bundle is not a graph merge, but an overlay, and is separated from existing groups.”

## Assumptions

- The checker decision starts with a shape parser-based heuristic in the initial implementation.
- Accurate shapez 2 checker rule advancement and config file creation are separated into Phase 3.
- Obtain human approval again before subsequent implementation.
