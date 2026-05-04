from __future__ import annotations

from collections import defaultdict, deque

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_render_scene import build_shape_render_scene
from django_apps.shapez_solver.domain.batch_plan import BatchPlan
from django_apps.shapez_solver.domain.flow_graph import FlowEdge, FlowGraph, FlowNode
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


def build_flow_graph_from_batch_plan(plan: BatchPlan) -> FlowGraph:
    """BatchPlan을 단순 단계별 FlowGraph(요약)로 만든다."""

    nodes: list[FlowNode] = []
    edges: list[FlowEdge] = []
    for shape_code, quantity in sorted(plan.sources.items()):
        node_id = f"flow-src-{shape_code}"
        nodes.append(
            FlowNode(
                id=node_id,
                kind="source",
                label=f"Source x{quantity}",
                shape_code=shape_code,
                quantity=quantity,
                stage_index=0,
            )
        )
    for run in plan.steps:
        nodes.append(
            FlowNode(
                id=f"flow-op-{run.id}",
                kind="operation",
                label=OPERATION_CATALOG[run.operation].label,
                operation=run.operation,
                quantity=1,
                stage_index=run.stage_index,
            )
        )
    return FlowGraph(nodes=tuple(nodes), edges=tuple(edges))


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
        target_preview = (
            _preview_from_code(display_target_shape.canonical_code)
            if display_target_shape is not None
            else _preview_from_code(display_target_shape_code)
        )
        graph_nodes.append(
            SolverShapeNode(
                id="inv-target-primary",
                role="target",
                shape_code=display_target_shape_code,
                label=f"Target x{plan.target_count}" if plan.target_count > 1 else "Target",
                preview_scene=target_preview,
                quantity=plan.target_count,
            )
        )
        return SolverGraph(nodes=tuple(graph_nodes), edges=tuple(graph_edges))

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
            graph_edges.append(
                SolverGraphEdge(
                    from_id=source_id,
                    to_id=op_id,
                    kind="input",
                    slot=f"Input {chr(ord('A') + slot_index)}",
                    label=f"Input {chr(ord('A') + slot_index)}",
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
            graph_edges.append(
                SolverGraphEdge(
                    from_id=op_id,
                    to_id=out_id,
                    kind="output",
                    slot=f"Output {chr(ord('A') + slot_index)}",
                    label=f"Output {chr(ord('A') + slot_index)}",
                    quantity=1,
                )
            )

    target_preview = (
        _preview_from_code(display_target_shape.canonical_code)
        if display_target_shape is not None
        else _preview_from_code(display_target_shape_code)
    )
    target_id = "inv-target-primary"
    graph_nodes.append(
        SolverShapeNode(
            id=target_id,
            role="target",
            shape_code=display_target_shape_code,
            label=f"Target x{plan.target_count}" if plan.target_count > 1 else "Target",
            preview_scene=target_preview,
            quantity=plan.target_count,
        )
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
