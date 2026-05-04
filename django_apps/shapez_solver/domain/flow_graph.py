from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_solver.domain.operations import OperationType


@dataclass(frozen=True, slots=True)
class FlowNode:
    """Batch flow graph의 source, operation, target, waste 노드."""

    id: str
    kind: str
    label: str
    shape_code: str = ""
    operation: OperationType | None = None
    quantity: int = 0
    stage_index: int = 0


@dataclass(frozen=True, slots=True)
class FlowEdge:
    """Batch flow graph에서 quantity를 갖는 shape 이동."""

    from_id: str
    to_id: str
    shape_code: str
    quantity: int


@dataclass(frozen=True, slots=True)
class FlowGraph:
    """BatchPlan에서 직접 생성되는 flow graph."""

    nodes: tuple[FlowNode, ...]
    edges: tuple[FlowEdge, ...]
