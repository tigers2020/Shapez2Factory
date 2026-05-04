"""Unused BatchPlan → FlowGraph summary scaffold (legacy; no active callers)."""

from __future__ import annotations

from django_apps.shapez_solver.domain.batch_plan import BatchPlan
from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.legacy.flow_graph import FlowEdge, FlowGraph, FlowNode


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
