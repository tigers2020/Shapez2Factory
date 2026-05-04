from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.domain.search_cost import SearchCost


@dataclass(frozen=True, slots=True)
class Action:
    """Inventory search에서 한 번 실행할 operation 후보."""

    operation: OperationType
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    cost: SearchCost
    label: str = ""
    macro_kind: str = ""
    macro_source: str = ""
    primitive_chain: tuple[Action, ...] | None = None


@dataclass(frozen=True, slots=True)
class OperationRun:
    """BatchPlan에 기록되는 실제 operation 실행."""

    id: str
    operation: OperationType
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    stage_index: int
    run_index: int
    macro_kind: str = ""
    macro_source: str = ""
