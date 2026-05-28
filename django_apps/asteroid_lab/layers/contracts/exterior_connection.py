"""Layer 02 exterior connection plan DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


class ExteriorConnectionShortfallReason(StrEnum):
    MISSING_EVTC_ROW = "missing_evtc_row"
    TARGET_EXCEEDS_TERRAIN_UPPER_BOUND = "target_exceeds_terrain_upper_bound"
    NO_FEASIBLE_CONNECTOR_SITES = "no_feasible_connector_sites"


@dataclass(frozen=True, slots=True)
class ExteriorConnector:
    connector_id: str
    void_coord: Coord
    edge: CardinalEdge
    layout_t: str
    rotation: int
    capacity_per_min: Decimal
    coords: tuple[Coord, ...]


@dataclass(frozen=True, slots=True)
class ExteriorConnectionPlan:
    transport_kind: str
    terrain_upper_bound_per_min: Decimal
    planning_target_per_min: Decimal
    per_connector_capacity_per_min: Decimal
    required_connector_count: int
    planned_connectors: tuple[ExteriorConnector, ...]
    unmet_reason: ExteriorConnectionShortfallReason | None
    slot_rule: str = "VOID_DEEP_SLOTS_V1"
    placement_rule: str = "EDGE_WEIGHTED_EVEN_SPACING_V1"
    rotation_rule: str = "FIELDWARD_FACING_V1"


__all__ = [
    "ExteriorConnectionPlan",
    "ExteriorConnectionShortfallReason",
    "ExteriorConnector",
]
