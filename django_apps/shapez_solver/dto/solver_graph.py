from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

type GraphNodeKind = Literal["shape", "operation"]
type ShapeNodeRole = Literal["source", "intermediate", "target"]
type GraphEdgeKind = Literal["input", "output"]
type ShapeProducedState = Literal["consumed", "unused", "target"]


@dataclass(frozen=True, slots=True)
class SolverShapeNode:
    id: str
    role: ShapeNodeRole
    shape_code: str
    label: str
    preview_scene: dict[str, Any] | None = None
    reused_count: int = 0
    quantity: int = 1
    produced_state: ShapeProducedState | None = None
    batch_index: int | None = None
    batch_total: int | None = None
    kind: Literal["shape"] = field(default="shape", init=False)


@dataclass(frozen=True, slots=True)
class SolverOperationNode:
    id: str
    operation_type: str
    label: str
    icon: str
    input_count: int
    output_count: int
    description: str
    run_index: int | None = None
    run_total: int | None = None
    kind: Literal["operation"] = field(default="operation", init=False)


type SolverGraphNode = SolverShapeNode | SolverOperationNode


@dataclass(frozen=True, slots=True)
class SolverGraphEdge:
    from_id: str
    to_id: str
    kind: GraphEdgeKind
    slot: str | None = None
    label: str | None = None
    quantity: int = 1


@dataclass(frozen=True, slots=True)
class SolverGraph:
    nodes: tuple[SolverGraphNode, ...]
    edges: tuple[SolverGraphEdge, ...]
    direction: Literal["left-to-right"] = "left-to-right"
