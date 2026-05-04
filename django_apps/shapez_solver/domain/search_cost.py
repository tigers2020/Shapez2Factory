from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True, slots=True)
class SearchCost:
    """Dijkstra priority queue에서 비교 가능한 cost tuple."""

    operation_runs: int = 0
    factory_depth: int = 0
    waste_count: int = 0
    graph_complexity: int = 0

    def __add__(self, other: SearchCost) -> SearchCost:
        return SearchCost(
            operation_runs=self.operation_runs + other.operation_runs,
            factory_depth=self.factory_depth + other.factory_depth,
            waste_count=self.waste_count + other.waste_count,
            graph_complexity=self.graph_complexity + other.graph_complexity,
        )

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (
            self.operation_runs,
            self.factory_depth,
            self.waste_count,
            self.graph_complexity,
        )


DEFAULT_OPERATION_COST = SearchCost(operation_runs=1, factory_depth=1)
ZERO_SEARCH_COST = SearchCost()
