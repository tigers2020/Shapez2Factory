"""Layer 03 rim bundle generation tests (PR-3b)."""

from __future__ import annotations

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    EXPECTED_INTRINSIC_PRIORITY_RANK_ORDER,
)
from django_apps.asteroid_lab.layers.contracts.candidates import (
    CandidateRejectReason,
    Layer03SkipReason,
    RouteProbeStatus,
)
from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.route_goal import (
    RouteGoal,
    RouteGoalKind,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import ResourceKind, TransportKind
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.expand import (
    expand_rim_bundle_candidates,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.project import (
    project_miner_seed_at_anchor,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.rim_anchors import (
    select_exterior_output_dir,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_catalog import (
    MinerSeedCatalog,
    MinerSeedEntry,
    load_miner_seed_catalog,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.reconstruction.rim_topology import field_rim_cells
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    expected_golden_rim_anchor_count,
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
    two_seed_catalog,
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


def test_select_exterior_output_dir_prefers_closer_route_goal() -> None:
    anchor = (5, 5)
    complete_map = _minimal_complete_map(
        field_cells=frozenset({anchor}),
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
    direction = select_exterior_output_dir(
        anchor,
        complete_map=complete_map,
        route_goals=goals,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert direction == Direction.N


def test_select_exterior_output_dir_tiebreak_nesw() -> None:
    anchor = (5, 5)
    complete_map = _minimal_complete_map(
        field_cells=frozenset({anchor}),
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
    direction = select_exterior_output_dir(
        anchor,
        complete_map=complete_map,
        route_goals=goals,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert direction == Direction.N


def test_no_exterior_direction_when_all_cardinals_on_field() -> None:
    anchor = (5, 5)
    complete_map = _minimal_complete_map(
        field_cells=frozenset(
            {
                anchor,
                (5, 4),
                (6, 5),
                (5, 6),
                (4, 5),
            },
        ),
        external_void_cells=frozenset({(99, 99)}),
    )
    direction = select_exterior_output_dir(
        anchor,
        complete_map=complete_map,
        route_goals=(),
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert direction is None


def _minimal_seed_decoded_json() -> dict[str, object]:
    return {
        "BP": {
            "Entries": [
                {"T": "Layout_ShapeMiner", "X": 0, "Y": 0, "R": 0},
                {"T": "SpaceBelt_Forward", "X": 1, "Y": 0, "R": 0},
                {"T": "SpaceBelt_Forward", "X": 2, "Y": 0, "R": 0},
            ],
        },
    }


def _single_seed_catalog() -> MinerSeedCatalog:
    return MinerSeedCatalog.from_entries(
        MinerSeedEntry(
            gene_key="miner_seed_m0e_01",
            pattern_id="m0e_01",
            intrinsic_priority_rank=18,
            throughput_factor=4,
            topology_signature="topo_m0e",
            decoded_json=_minimal_seed_decoded_json(),
        ),
    )


@pytest.mark.django_db
def test_load_miner_seed_catalog_sorted_by_intrinsic_priority() -> None:
    call_command("seed_miner_patterns", replace_stale=True)
    catalog = load_miner_seed_catalog()
    ranks = [s.intrinsic_priority_rank for s in catalog.seeds]
    assert ranks == sorted(ranks)
    assert catalog.seeds[0].pattern_id == EXPECTED_INTRINSIC_PRIORITY_RANK_ORDER[0]


def test_mining_cells_subset_of_field_cells() -> None:
    complete_map = golden_5x5_complete_map()
    anchor = (6, 4)
    seed = _single_seed_catalog().seeds[0]
    projection = project_miner_seed_at_anchor(
        seed=seed,
        anchor_coord=anchor,
        output_dir=Direction.E,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=complete_map,
    )
    assert projection.candidate is not None
    assert projection.reject_reason is None
    assert projection.candidate.mining_occupied_cells <= complete_map.field_cells


def test_transport_stub_subset_of_void() -> None:
    complete_map = golden_5x5_complete_map()
    anchor = (6, 4)
    projection = project_miner_seed_at_anchor(
        seed=_single_seed_catalog().seeds[0],
        anchor_coord=anchor,
        output_dir=Direction.E,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=complete_map,
    )
    assert projection.candidate is not None
    candidate = projection.candidate
    assert candidate.transport_stub_cells <= complete_map.external_void_cells
    assert candidate.mining_occupied_cells.isdisjoint(candidate.transport_stub_cells)


def test_anchor_on_outer_rim() -> None:
    complete_map = golden_5x5_complete_map()
    anchor = (6, 4)
    projection = project_miner_seed_at_anchor(
        seed=_single_seed_catalog().seeds[0],
        anchor_coord=anchor,
        output_dir=Direction.E,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=complete_map,
    )
    rim = field_rim_cells(complete_map.field_cells)
    assert projection.candidate is not None
    assert projection.candidate.anchor_coord in rim


def test_projection_failure_returns_reject_reason() -> None:
    complete_map = golden_5x5_complete_map()
    bad_seed = MinerSeedEntry(
        gene_key="miner_seed_bad",
        pattern_id="bad",
        intrinsic_priority_rank=99,
        throughput_factor=4,
        topology_signature="bad",
        decoded_json={"BP": {"Entries": [{"T": "SpaceBelt_Forward", "X": 0, "Y": 0, "R": 0}]}},
    )
    projection = project_miner_seed_at_anchor(
        seed=bad_seed,
        anchor_coord=(2, 4),
        output_dir=Direction.E,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=complete_map,
    )
    assert projection.candidate is None
    assert projection.reject_reason == CandidateRejectReason.LOCAL_GEOMETRY_INVALID


def test_build_rim_bundle_candidate_set_requires_observability() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        Layer03ExpansionMetrics,
        Layer03SkipReason,
        build_rim_bundle_candidate_set,
    )
    from django_apps.asteroid_lab.layers.contracts.layer03_observability import (
        build_layer03_observability_for_test,
    )

    obs = build_layer03_observability_for_test(skip_reason=Layer03SkipReason.NONE)
    result = build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics.empty(),
        observability=obs,
    )
    assert result.observability.skip_reason is Layer03SkipReason.NONE


def test_expand_populates_layer03_observability() -> None:
    result = expand_rim_bundle_candidates(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=two_seed_catalog(),
    )
    assert result.observability.normal_candidate_count == result.metrics.normal_candidate_count
    assert result.observability.skip_reason == result.metrics.layer_skip_reason
    from django_apps.asteroid_lab.layers.contracts.layer03_observability import (
        sort_replay_pool_candidates,
    )

    assert len(result.observability.replay_pool_candidates) == len(result.normal_candidates)
    assert result.observability.replay_pool_candidates == sort_replay_pool_candidates(
        result.normal_candidates
    )


def test_expand_empty_miner_seed_catalog_hold() -> None:
    result = expand_rim_bundle_candidates(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=MinerSeedCatalog(seeds=()),
    )
    assert result.metrics.layer_skip_reason == Layer03SkipReason.EMPTY_MINER_SEED_CATALOG
    assert result.metrics.rim_anchor_count == expected_golden_rim_anchor_count()
    assert result.metrics.seed_projection_attempt_count == 0
    assert result.normal_candidates == ()


def test_expand_rim_candidates_deterministic_count() -> None:
    result = expand_rim_bundle_candidates(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=two_seed_catalog(),
    )
    assert result.metrics.rim_anchor_count == expected_golden_rim_anchor_count()
    assert result.metrics.seed_projection_attempt_count > 0
    assert all(c.route_probe_status == RouteProbeStatus.SUCCEEDED for c in result.normal_candidates)
    assert result.metrics.normal_candidate_count == len(result.normal_candidates)


def test_duplicate_equivalence_keeps_lower_intrinsic_priority_rank() -> None:
    catalog = two_seed_catalog()
    complete_map = golden_5x5_complete_map()
    result = expand_rim_bundle_candidates(
        complete_map=complete_map,
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=catalog,
    )
    assert result.metrics.dedupe_duplicate_count > 0
    winners = {c.candidate.equivalence_key: c for c in result.normal_candidates}
    assert len(winners) == result.metrics.normal_candidate_count
    for probed in result.normal_candidates:
        assert probed.candidate.pattern_id == "m3e_01"
