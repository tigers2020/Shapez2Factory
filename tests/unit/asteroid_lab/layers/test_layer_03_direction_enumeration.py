"""Layer 03 R2-lite exterior direction enumeration."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.route_goal import (
    RouteGoal,
    RouteGoalKind,
    build_layer03_route_goals,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.expand import (
    expand_rim_bundle_candidates,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.project import (
    project_miner_seed_at_anchor,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.rim_anchors import (
    exterior_output_dir_candidates,
    select_exterior_output_dir,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_catalog import (
    MinerSeedCatalog,
    MinerSeedEntry,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.transport_entry import (
    derive_transport_entry_coord,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord
from tests.unit.asteroid_lab.layers.fixtures.layer_03_eeemb_projection import (
    eeemb_complete_map,
    eeemb_seed_entry,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_r1_fail_r2_success import (
    eeemb_seed_entry as r2_eeemb_seed,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_r1_fail_r2_success import (
    r1_fail_r2_success_complete_map,
    r1_fail_r2_success_l2_plan,
)


def _minimal_complete_map(
    *,
    field_cells: frozenset[Coord],
    external_void_cells: frozenset[Coord],
) -> ReconstructionCompleteMap:
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field_cells,
        shape_field_cell_count=len(field_cells),
        fluid_field_cell_count=0,
        external_void_cells=external_void_cells,
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def test_exterior_output_dir_candidates_includes_all_non_field_cardinals() -> None:
    anchor = (5, 5)
    complete_map = _minimal_complete_map(
        field_cells=frozenset({anchor}),
        external_void_cells=frozenset({(5, 4), (6, 5), (99, 99)}),
    )
    dirs = exterior_output_dir_candidates(
        anchor,
        complete_map=complete_map,
        route_goals=(),
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert set(dirs) == {Direction.N, Direction.E, Direction.S, Direction.W}


def test_exterior_output_dir_candidates_sorted_by_goal_not_truncated() -> None:
    anchor = (5, 5)
    complete_map = _minimal_complete_map(
        field_cells=frozenset({anchor, (5, 6), (4, 5)}),
        external_void_cells=frozenset({(5, 4), (6, 5)}),
    )
    goals = (
        RouteGoal(
            goal_id="north",
            kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
            coord=(5, 4),
            transport_kind=TransportKind.SHAPE_BELT,
            priority=0,
            connector_role=ExteriorConnectorRole.REQUIRED,
        ),
        RouteGoal(
            goal_id="east",
            kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
            coord=(6, 5),
            transport_kind=TransportKind.SHAPE_BELT,
            priority=0,
            connector_role=ExteriorConnectorRole.REQUIRED,
        ),
    )
    dirs = exterior_output_dir_candidates(
        anchor,
        complete_map=complete_map,
        route_goals=goals,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert len(dirs) == 2
    assert dirs[0] == select_exterior_output_dir(
        anchor,
        complete_map=complete_map,
        route_goals=goals,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert set(dirs) == {Direction.S, Direction.E}


def test_exterior_output_dir_candidate_places_stub_in_physical_void() -> None:
    anchor = (5, 5)
    complete_map = _minimal_complete_map(
        field_cells=frozenset({anchor, (5, 6), (4, 5), (6, 5)}),
        external_void_cells=frozenset({(5, 4)}),
    )
    goals = (
        RouteGoal(
            goal_id="north",
            kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
            coord=(5, 4),
            transport_kind=TransportKind.SHAPE_BELT,
            priority=0,
            connector_role=ExteriorConnectorRole.REQUIRED,
        ),
    )
    output_dir = select_exterior_output_dir(
        anchor,
        complete_map=complete_map,
        route_goals=goals,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert output_dir is Direction.S
    assert derive_transport_entry_coord(anchor_coord=anchor, output_dir=output_dir) == (5, 4)


def test_eeemb_projection_m_anchor_output_dir_e() -> None:
    result = project_miner_seed_at_anchor(
        seed=eeemb_seed_entry(),
        anchor_coord=(7, 3),
        output_dir=Direction.E,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=eeemb_complete_map(),
    )
    assert result.candidate is not None
    assert result.reject_reason is None
    candidate = result.candidate
    assert candidate.anchor_coord == (7, 3)
    assert candidate.mining_occupied_cells <= eeemb_complete_map().field_cells
    assert candidate.transport_stub_cells & eeemb_complete_map().field_cells == frozenset()
    assert (4, 3) in candidate.mining_occupied_cells
    assert (8, 3) in candidate.transport_stub_cells


def test_r2_lite_finds_e_direction_when_r1_would_pick_n_only() -> None:
    anchor = (7, 3)
    complete_map = r1_fail_r2_success_complete_map()
    plan = r1_fail_r2_success_l2_plan()
    goals = build_layer03_route_goals(plan, transport_kind=TransportKind.SHAPE_BELT)
    assert (
        select_exterior_output_dir(
            anchor,
            complete_map=complete_map,
            route_goals=goals,
            transport_kind=TransportKind.SHAPE_BELT,
        )
        == Direction.S
    )
    dirs = exterior_output_dir_candidates(
        anchor,
        complete_map=complete_map,
        route_goals=goals,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert Direction.S in dirs and Direction.E in dirs

    result = expand_rim_bundle_candidates(
        complete_map=complete_map,
        exterior_plan=plan,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=MinerSeedCatalog.from_entries(r2_eeemb_seed()),
    )
    assert result.metrics.route_probe_attempt_count > 0


def test_expand_reports_direction_seed_attempt_count() -> None:
    result = expand_rim_bundle_candidates(
        complete_map=r1_fail_r2_success_complete_map(),
        exterior_plan=r1_fail_r2_success_l2_plan(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=MinerSeedCatalog.from_entries(r2_eeemb_seed()),
    )
    assert result.metrics.direction_seed_attempt_count >= 2
    assert result.metrics.exterior_direction_candidate_count >= 2


def test_local_geometry_invalid_subreason_in_histogram() -> None:
    no_extractor = MinerSeedEntry(
        gene_key="no_extractor",
        pattern_id="bad",
        intrinsic_priority_rank=1,
        throughput_factor=16,
        topology_signature="topo_bad",
        decoded_json={
            "BP": {
                "Entries": [
                    {"T": "SpaceBelt_Forward", "X": 0, "Y": 0, "R": 0},
                ],
            },
        },
    )
    complete_map = _minimal_complete_map(
        field_cells=frozenset({(5, 5)}),
        external_void_cells=frozenset({(5, 4)}),
    )
    result = expand_rim_bundle_candidates(
        complete_map=complete_map,
        exterior_plan=r1_fail_r2_success_l2_plan(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=MinerSeedCatalog.from_entries(no_extractor),
    )
    counts = dict(result.metrics.reject_reason_counts)
    assert counts.get("local_geometry_invalid.missing_extractor", 0) >= 1
