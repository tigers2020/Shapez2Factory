from __future__ import annotations

from collections import defaultdict, deque

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_render_scene import build_shape_render_scene
from django_apps.shapez_solver.domain.batch_plan import BatchPlan
from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.dto.solver_graph import (
    SolverGraph,
    SolverGraphEdge,
    SolverGraphNode,
    SolverOperationNode,
    SolverShapeNode,
)


def _preview_from_code(shape_code: str) -> dict[str, object]:
    pattern = parse_shape_code_list(shape_code)[0]
    scene = build_shape_render_scene(pattern)
    return {
        "normalized_code": scene.normalized_code,
        "cells": [
            {
                "layer_index": cell.layer_index,
                "quadrant_index": cell.quadrant_index,
                "position": cell.position.value,
                "shape_code": cell.shape_code,
                "color_code": cell.color_code,
                "shape_kind": cell.shape_kind,
                "color_kind": cell.color_kind,
                "mesh_key": cell.mesh_key,
                "material_key": cell.material_key,
                "transform_key": cell.transform_key,
            }
            for cell in scene.cells
        ],
    }


def _target_preview(
    display_target_shape: Shape | None,
    display_target_shape_code: str,
) -> dict[str, object]:
    if display_target_shape is not None:
        return _preview_from_code(display_target_shape.canonical_code)
    return _preview_from_code(display_target_shape_code)


def _target_shape_node(
    display_target_shape_code: str,
    plan: BatchPlan,
    preview_scene: dict[str, object],
) -> SolverShapeNode:
    label = f"Target x{plan.target_count}" if plan.target_count > 1 else "Target"
    return SolverShapeNode(
        id="inv-target-primary",
        role="target",
        shape_code=display_target_shape_code,
        label=label,
        preview_scene=preview_scene,
        quantity=plan.target_count,
    )


def _append_inventory_sources(
    plan: BatchPlan,
    graph_nodes: list[SolverGraphNode],
) -> dict[str, deque[str]]:
    pools: dict[str, deque[str]] = defaultdict(deque)
    for shape_code, quantity in plan.sources.items():
        node_id = f"inv-src-{shape_code}"
        for _ in range(quantity):
            pools[shape_code].append(node_id)
        graph_nodes.append(
            SolverShapeNode(
                id=node_id,
                role="source",
                shape_code=shape_code,
                label="Source",
                preview_scene=_preview_from_code(shape_code),
                quantity=quantity,
            )
        )
    return pools


def _append_steps_edges(
    plan: BatchPlan,
    pools: dict[str, deque[str]],
    graph_nodes: list[SolverGraphNode],
    graph_edges: list[SolverGraphEdge],
) -> None:
    for run in plan.steps:
        catalog = OPERATION_CATALOG[run.operation]
        op_id = f"inv-op-{run.id}"
        graph_nodes.append(
            SolverOperationNode(
                id=op_id,
                operation_type=catalog.type.value,
                label=catalog.label,
                icon=catalog.icon,
                input_count=catalog.input_count,
                output_count=catalog.output_count,
                description=catalog.description,
                run_index=run.run_index,
                run_total=len(plan.steps),
            )
        )
        for slot_index, shape_code in enumerate(run.inputs):
            source_id = pools[shape_code].popleft()
            slot = f"Input {chr(ord('A') + slot_index)}"
            graph_edges.append(
                SolverGraphEdge(
                    from_id=source_id,
                    to_id=op_id,
                    kind="input",
                    slot=slot,
                    label=slot,
                    quantity=1,
                )
            )
        for slot_index, shape_code in enumerate(run.outputs):
            out_id = f"inv-out-{run.id}-{slot_index}-{shape_code}"
            pools[shape_code].append(out_id)
            graph_nodes.append(
                SolverShapeNode(
                    id=out_id,
                    role="intermediate",
                    shape_code=shape_code,
                    label="Shape",
                    preview_scene=_preview_from_code(shape_code),
                    quantity=1,
                )
            )
            slot = f"Output {chr(ord('A') + slot_index)}"
            graph_edges.append(
                SolverGraphEdge(
                    from_id=op_id,
                    to_id=out_id,
                    kind="output",
                    slot=slot,
                    label=slot,
                    quantity=1,
                )
            )


def build_solver_graph_from_batch_plan(
    plan: BatchPlan,
    *,
    display_target_shape_code: str,
    display_target_shape: Shape | None = None,
) -> SolverGraph:
    """BatchPlan을 연결된 SolverGraph로 변환한다."""

    graph_nodes: list[SolverGraphNode] = []
    graph_edges: list[SolverGraphEdge] = []

    if not plan.steps:
        target_preview = _target_preview(display_target_shape, display_target_shape_code)
        graph_nodes.append(
            _target_shape_node(display_target_shape_code, plan, target_preview),
        )
        return SolverGraph(nodes=tuple(graph_nodes), edges=tuple(graph_edges))

    pools = _append_inventory_sources(plan, graph_nodes)
    _append_steps_edges(plan, pools, graph_nodes, graph_edges)

    target_preview = _target_preview(display_target_shape, display_target_shape_code)
    target_id = "inv-target-primary"
    graph_nodes.append(
        _target_shape_node(display_target_shape_code, plan, target_preview),
    )
    for _ in range(plan.target_count):
        donor_id = pools[plan.target_code].popleft()
        graph_edges.append(
            SolverGraphEdge(
                from_id=donor_id,
                to_id=target_id,
                kind="output",
                label="Target",
                quantity=1,
            )
        )

    return SolverGraph(nodes=tuple(graph_nodes), edges=tuple(graph_edges))
