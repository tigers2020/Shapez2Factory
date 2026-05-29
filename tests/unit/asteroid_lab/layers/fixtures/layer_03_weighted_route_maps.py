"""Fixtures for weighted L3 route probe (exterior vs field cost)."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.layers.contracts.candidates import make_bundle_candidate_for_test
from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnector,
)
from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from django_apps.asteroid_lab.layers.contracts.route_goal import RouteGoal, RouteGoalKind
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.exterior_domain import (
    build_weighted_transport_route_domain,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_catalog import (
    MinerSeedCatalog,
    MinerSeedEntry,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_ANCHOR: Coord = (2, 5)
_ENTRY: Coord = (3, 5)


def exterior_preferred_complete_map() -> ReconstructionCompleteMap:
    """Field strip at x=2,3 y=5; void corridor west and east; goal (0,2)."""
    field = frozenset({_ANCHOR, _ENTRY})
    void = frozenset(
        {
            (0, 2),
            (0, 3),
            (0, 4),
            (0, 5),
            (1, 2),
            (1, 3),
            (1, 4),
            (1, 5),
            (2, 2),
            (2, 3),
            (2, 4),
            (4, 2),
            (4, 3),
            (4, 4),
            (4, 5),
        },
    )
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=void,
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def exterior_preferred_goal() -> RouteGoal:
    return RouteGoal(
        goal_id="west_void",
        kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
        coord=(0, 2),
        transport_kind=TransportKind.SHAPE_BELT,
        priority=0,
        connector_role=ExteriorConnectorRole.REQUIRED,
    )


def exterior_preferred_probe_setup():
    complete_map = exterior_preferred_complete_map()
    goals = (exterior_preferred_goal(),)
    mining = frozenset({_ANCHOR})
    candidate = make_bundle_candidate_for_test(
        anchor_coord=_ANCHOR,
        mining_occupied_cells=mining,
        transport_stub_cells=frozenset(),
        route_probe_start_coord=_ENTRY,
    )
    domain = build_weighted_transport_route_domain(
        complete_map=complete_map,
        anchor_abs=_ANCHOR,
        transport_entry_coord=_ENTRY,
        transport_stub_cells=frozenset(),
        route_goals=goals,
        mining_occupied_cells=mining,
    )
    return complete_map, goals, candidate, domain


def field_only_complete_map() -> ReconstructionCompleteMap:
    """Solid field block x=2..3 y=2..5; goal (2,2) reachable only through field."""
    field = frozenset(
        {
            (2, 2),
            (2, 3),
            (2, 4),
            (2, 5),
            (3, 2),
            (3, 3),
            (3, 4),
            (3, 5),
        },
    )
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=frozenset(),
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def field_only_probe_setup():
    complete_map = field_only_complete_map()
    goals = (
        RouteGoal(
            goal_id="field_goal",
            kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
            coord=(2, 2),
            transport_kind=TransportKind.SHAPE_BELT,
            priority=0,
            connector_role=ExteriorConnectorRole.REQUIRED,
        ),
    )
    mining = frozenset({_ANCHOR})
    candidate = make_bundle_candidate_for_test(
        anchor_coord=_ANCHOR,
        mining_occupied_cells=mining,
        transport_stub_cells=frozenset(),
        route_probe_start_coord=_ENTRY,
    )
    domain = build_weighted_transport_route_domain(
        complete_map=complete_map,
        anchor_abs=_ANCHOR,
        transport_entry_coord=_ENTRY,
        transport_stub_cells=frozenset(),
        route_goals=goals,
        mining_occupied_cells=mining,
    )
    return complete_map, goals, candidate, domain


def no_stub_entry_complete_map() -> ReconstructionCompleteMap:
    """Rim strip + void north; entry (3,5) on field without preinstalled belt."""
    field = frozenset({(2, 5), (3, 5)})
    void = frozenset({(2, 2), (2, 3), (2, 4), (3, 4), (4, 5)})
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=void,
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def no_stub_entry_l2_plan() -> ExteriorConnectionPlan:
    return ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        planning_target_per_min=Decimal("5000"),
        per_connector_capacity_per_min=Decimal("1000"),
        required_connector_count=1,
        reference_connector_count=1,
        spare_connector_count=0,
        planned_connectors=(
            ExteriorConnector(
                connector_id="north_void",
                void_coord=(2, 2),
                edge=CardinalEdge.NORTH,
                layout_t="SpaceBelt_Forward",
                rotation=0,
                capacity_per_min=Decimal("1000"),
                coords=((2, 2),),
                role=ExteriorConnectorRole.REQUIRED,
            ),
        ),
        unmet_reason=None,
    )


def no_stub_miner_only_seed() -> MinerSeedEntry:
    return MinerSeedEntry(
        gene_key="miner_only",
        pattern_id="miner_only",
        intrinsic_priority_rank=1,
        throughput_factor=16,
        topology_signature="miner_only",
        decoded_json={
            "BP": {
                "Entries": [
                    {"T": "Layout_ShapeMiner", "X": 0, "Y": 0, "R": 0},
                ],
            },
        },
    )


def no_stub_miner_only_catalog() -> MinerSeedCatalog:
    return MinerSeedCatalog.from_entries(no_stub_miner_only_seed())


__all__ = [
    "exterior_preferred_probe_setup",
    "field_only_probe_setup",
    "no_stub_entry_complete_map",
    "no_stub_entry_l2_plan",
    "no_stub_miner_only_catalog",
    "no_stub_miner_only_seed",
]
