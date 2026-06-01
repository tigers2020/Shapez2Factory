"""Union-find route groups with M-bundle capacity (Layer 04)."""

from __future__ import annotations

from dataclasses import dataclass, field

from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    RouteGroupSummary,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    RouteGoal,
    RouteGoalKind,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    TransportKind,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

TRUNK_GOAL_PRIORITY = 5


@dataclass
class _MutableRouteGroup:
    connector_ids: set[str] = field(default_factory=set)
    member_placement_ids: set[str] = field(default_factory=set)
    route_cells: set[Coord] = field(default_factory=set)
    used_m: int = 0

    @property
    def capacity_m(self) -> int:
        return 0  # set by registry


class RouteGroupRegistry:
    """Merge-aware groups: capacity = len(connectors) * unit_capacity_m."""

    def __init__(
        self,
        *,
        unit_capacity_m: int,
        transport_kind: TransportKind,
    ) -> None:
        self._unit_capacity_m = unit_capacity_m
        self._transport_kind = transport_kind
        self._parent: dict[str, str] = {}
        self._groups: dict[str, _MutableRouteGroup] = {}
        self._cell_to_group: dict[Coord, str] = {}

    def _ensure(self, group_id: str) -> _MutableRouteGroup:
        if group_id not in self._groups:
            self._groups[group_id] = _MutableRouteGroup()
            self._parent[group_id] = group_id
        return self._groups[group_id]

    def find(self, group_id: str) -> str:
        parent = self._parent.get(group_id, group_id)
        if parent != group_id:
            root = self.find(parent)
            self._parent[group_id] = root
            return root
        return group_id

    def union(self, left: str, right: str) -> str:
        root_l = self.find(left)
        root_r = self.find(right)
        if root_l == root_r:
            return root_l
        # deterministic: smaller id wins
        if root_r < root_l:
            root_l, root_r = root_r, root_l
        merged = self._groups[root_l]
        other = self._groups.pop(root_r)
        merged.connector_ids |= other.connector_ids
        merged.member_placement_ids |= other.member_placement_ids
        merged.route_cells |= other.route_cells
        merged.used_m += other.used_m
        for cell in merged.route_cells:
            self._cell_to_group[cell] = root_l
        self._parent[root_r] = root_l
        return root_l

    def capacity_m(self, group_id: str) -> int:
        root = self.find(group_id)
        group = self._groups[root]
        count = len(group.connector_ids)
        return max(count, 1) * self._unit_capacity_m

    def remaining_m(self, group_id: str) -> int:
        root = self.find(group_id)
        group = self._groups[root]
        return self.capacity_m(root) - group.used_m

    def group_at_cell(self, coord: Coord) -> str | None:
        gid = self._cell_to_group.get(coord)
        if gid is None:
            return None
        return self.find(gid)

    def connector_group(self, connector_id: str) -> str:
        gid = f"conn_{connector_id}"
        self._ensure(gid)
        self._groups[gid].connector_ids.add(connector_id)
        return gid

    def trunk_goals(self) -> tuple[RouteGoal, ...]:
        goals: list[RouteGoal] = []
        seen: set[Coord] = set()
        for cell, gid in sorted(self._cell_to_group.items()):
            root = self.find(gid)
            if self.remaining_m(root) <= 0:
                continue
            if cell in seen:
                continue
            seen.add(cell)
            goals.append(
                RouteGoal(
                    goal_id=f"trunk_{root}_{cell[0]}_{cell[1]}",
                    kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
                    coord=cell,
                    transport_kind=self._transport_kind,
                    priority=TRUNK_GOAL_PRIORITY,
                    connector_role=ExteriorConnectorRole.REQUIRED,
                )
            )
        goals.sort(key=lambda g: (g.priority, g.goal_id))
        return tuple(goals)

    def commit_path(
        self,
        *,
        path: tuple[Coord, ...],
        placement_id: str,
        connector_id: str | None,
        source_load_m: int,
    ) -> str:
        if connector_id is not None:
            primary = self.connector_group(connector_id)
        elif path:
            last = path[-1]
            primary = self._cell_to_group.get(last, f"orphan_{placement_id}")
            self._ensure(primary)
        else:
            primary = f"orphan_{placement_id}"
            self._ensure(primary)

        for cell in path:
            existing = self._cell_to_group.get(cell)
            if existing is not None:
                primary = self.union(primary, existing)
            self._cell_to_group[cell] = primary

        group = self._groups[self.find(primary)]
        if connector_id is not None:
            group.connector_ids.add(connector_id)
        group.member_placement_ids.add(placement_id)
        group.route_cells |= set(path)
        group.used_m += source_load_m
        return self.find(primary)

    def summaries(self, *, transport_kind_slug: str) -> tuple[RouteGroupSummary, ...]:
        roots = {self.find(gid) for gid in self._groups}
        out: list[RouteGroupSummary] = []
        for root in sorted(roots):
            group = self._groups[root]
            out.append(
                RouteGroupSummary(
                    group_id=root,
                    transport_kind=transport_kind_slug,
                    connector_ids=frozenset(group.connector_ids),
                    member_placement_ids=frozenset(group.member_placement_ids),
                    route_cells=frozenset(group.route_cells),
                    used_m=group.used_m,
                    capacity_m=self.capacity_m(root),
                )
            )
        return tuple(out)


__all__ = [
    "RouteGroupRegistry",
    "TRUNK_GOAL_PRIORITY",
]
