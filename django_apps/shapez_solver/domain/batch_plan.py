from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_solver.domain.search_action import OperationRun
from django_apps.shapez_solver.domain.search_cost import SearchCost


@dataclass(frozen=True, slots=True)
class BatchPlan:
    """Batch-aware solver가 반환하는 operation plan."""

    target_code: str
    target_count: int
    sources: dict[str, int]
    steps: tuple[OperationRun, ...]
    final_inventory: dict[str, int]
    cost: SearchCost
    states_explored: int
    used_macro_kinds: tuple[str, ...] = ()
    used_macro_sources: tuple[str, ...] = ()
