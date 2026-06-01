"""Layer 05 transport routing contracts (canonical; was misnumbered layer04)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

LAYER05_ROUTE_PLAN_VERSION = "layer05_route_plan_v1"
DEPRECATED_LAYER04_ROUTE_PLAN_VERSION = "layer04_route_plan_v1"
_SUPPORTED_ROUTE_PLAN_VERSIONS = frozenset(
    {LAYER05_ROUTE_PLAN_VERSION, DEPRECATED_LAYER04_ROUTE_PLAN_VERSION}
)


class Layer05FailureReason(StrEnum):
    MISSING_L2_EXTERIOR_PLAN = "missing_l2_exterior_plan"
    EMPTY_L3_PACKAGE = "empty_l3_package"
    RESOURCE_KIND_MISMATCH = "resource_kind_mismatch"
    MIX_UNSUPPORTED = "mix_unsupported"
    NO_CONNECTOR_WITH_CAPACITY = "no_connector_with_capacity"
    ROUTE_NOT_FOUND = "route_not_found"
    CAPACITY_OVERFLOW = "capacity_overflow"
    COMMIT_OVERLAP_BLOCKED = "commit_overlap_blocked"
    CATALOG_MISSING_TILE = "catalog_missing_tile"
    UNSUPPORTED_IO_SIGNATURE = "unsupported_io_signature"


@dataclass(frozen=True, slots=True)
class Layer05SourceView:
    """L5 routing input per committed L3 placement (not raw ``IntegratedRimGreedyResult``)."""

    placement_id: str
    m_output_stub: Coord
    source_load_m: int
    throughput_factor: int
    equipment_cells: frozenset[Coord]
    route_probe_path: tuple[Coord, ...]


@dataclass(frozen=True, slots=True)
class CommittedRoute:
    route_id: str
    placement_id: str
    path_coords: tuple[Coord, ...]
    group_id: str
    route_cost: int


@dataclass(frozen=True, slots=True)
class RouteGroupSummary:
    group_id: str
    transport_kind: str
    connector_ids: frozenset[str]
    member_placement_ids: frozenset[str]
    route_cells: frozenset[Coord]
    used_m: int
    capacity_m: int


@dataclass(frozen=True, slots=True)
class ProjectedTransportTile:
    coord: Coord
    transport_kind: str
    tile_id: str
    rotation: int
    input_dirs: tuple[str, ...]
    output_dirs: tuple[str, ...]
    group_id: str
    source_route_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Layer05Failure:
    placement_id: str | None
    reason: Layer05FailureReason
    detail: str = ""


@dataclass(frozen=True, slots=True)
class Layer05Metrics:
    source_count: int = 0
    routed_source_count: int = 0
    failed_source_count: int = 0
    total_route_cells: int = 0
    total_route_cost: int = 0


@dataclass(frozen=True, slots=True)
class Layer05RoutePlan:
    version: str
    resource_kind: str
    transport_kind: str
    routes: tuple[CommittedRoute, ...]
    groups: tuple[RouteGroupSummary, ...]
    transport_tiles: tuple[ProjectedTransportTile, ...]
    failures: tuple[Layer05Failure, ...]
    metrics: Layer05Metrics

    @classmethod
    def empty(cls, *, resource_kind: str, transport_kind: str) -> Layer05RoutePlan:
        return cls(
            version=LAYER05_ROUTE_PLAN_VERSION,
            resource_kind=resource_kind,
            transport_kind=transport_kind,
            routes=(),
            groups=(),
            transport_tiles=(),
            failures=(),
            metrics=Layer05Metrics(),
        )


__all__ = [
    "DEPRECATED_LAYER04_ROUTE_PLAN_VERSION",
    "LAYER05_ROUTE_PLAN_VERSION",
    "CommittedRoute",
    "Layer05Failure",
    "Layer05FailureReason",
    "Layer05Metrics",
    "Layer05RoutePlan",
    "Layer05SourceView",
    "ProjectedTransportTile",
    "RouteGroupSummary",
]
