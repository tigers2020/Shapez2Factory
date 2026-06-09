"""PR-4: artifact-level golden eval tests."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_eval import (
    GoldenEvalResult,
    _connectivity_roots,
    evaluate_against_golden,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures import (
    golden_fixture_dir,
    load_empty_copy,
    load_game_data_rules,
    load_genetic_sample_seeds,
    load_golden_copy,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_loader import (
    GoldenOracle,
    build_golden_oracle,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run import (
    GoldenSolverArtifacts,
    GoldenSolverConfig,
    run_golden_solver,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnector,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    CommittedRoute,
    Layer05Metrics,
    Layer05RoutePlan,
    RouteGroupSummary,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_post_summary import (
    LayerPostSummaryOutcome,
    LayerPostSummaryRecord,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
    build_empty_integrated_rim_greedy_result,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.stack_result import (
    StackRunResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.stack_status import (
    StackRunStatus,
)
from shapez2_factory.application.asteroid_lab.stack_runner import CoreStackRunResult
from shapez2_factory.domain.asteroid_lab.coord_frames import CoordFrame
from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

_FIXTURE_ROOT = golden_fixture_dir()


def _fixtures_ready() -> bool:
    return all(
        (_FIXTURE_ROOT / name).is_file()
        for name in (
            "empty.shapez.txt",
            "golden.shapez.txt",
            "game_data_snapshot_min.json",
            "genetic_sample_seeds.json",
        )
    )


def _empty_oracle() -> GoldenOracle:
    return GoldenOracle(
        extractor_anchors_direct=frozenset({(1, 1), (2, 2)}),
        extractor_anchors_normalized=frozenset({(0, 0), (1, 1)}),
        extension_cells=frozenset({(0, 0)}),
        belt_edges=frozenset(),
        layout_miner_count=2,
        layout_extension_count=1,
        belt_count=0,
        entry_count=3,
        bbox=(0, 2, 0, 2),
    )


def _minimal_complete_map(
    *, void_cells: frozenset[Coord] | None = None
) -> ReconstructionCompleteMap:
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=frozenset(),
        shape_field_cell_count=0,
        fluid_field_cell_count=0,
        external_void_cells=void_cells or frozenset(),
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def _layer_summaries_completed() -> tuple[LayerPostSummaryRecord, ...]:
    return tuple(
        LayerPostSummaryRecord(
            layer_slug=slug,
            layer_index=index,
            outcome=LayerPostSummaryOutcome.COMPLETED,
            elapsed_ms=1,
            remaining_budget_ms=59_000,
            metrics={},
        )
        for index, slug in enumerate(
            (
                LAYER_02_EXTERIOR_TRANSPORT,
                LAYER_03_RIM_GREEDY_PLACEMENT,
                LAYER_04_INNER_PATTERN_FILL,
                LAYER_05_TRANSPORT_ROUTING,
            ),
            start=2,
        )
    )


def _exterior_plan() -> ExteriorConnectionPlan:
    connector = ExteriorConnector(
        connector_id="c0",
        void_coord=(0, 0),
        edge=CardinalEdge.NORTH,
        layout_t="Layout_ShapeMiner",
        rotation=0,
        capacity_per_min=Decimal("100"),
        coords=((0, 0), (0, 1)),
        role=ExteriorConnectorRole.REQUIRED,
    )
    return ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("1000"),
        planning_target_per_min=Decimal("800"),
        per_connector_capacity_per_min=Decimal("100"),
        required_connector_count=1,
        reference_connector_count=1,
        spare_connector_count=0,
        planned_connectors=(connector,),
        unmet_reason=None,
    )


def _valid_route_plan() -> Layer05RoutePlan:
    return Layer05RoutePlan(
        version="layer05_route_plan_v1",
        resource_kind="shape",
        transport_kind="shape",
        routes=(
            CommittedRoute(
                route_id="route_p0",
                placement_id="p0",
                path_coords=((1, 1), (2, 1)),
                group_id="g0",
                route_cost=2,
            ),
        ),
        groups=(
            RouteGroupSummary(
                group_id="g0",
                transport_kind="shape",
                connector_ids=frozenset({"c0"}),
                member_placement_ids=frozenset({"p0"}),
                route_cells=frozenset({(1, 1), (2, 1)}),
                used_m=16,
                capacity_m=100,
            ),
        ),
        transport_tiles=(),
        failures=(),
        metrics=Layer05Metrics(
            source_count=1,
            routed_source_count=1,
            failed_source_count=0,
            total_route_cells=2,
        ),
    )


def _rim_with_placement() -> object:
    placement = CommittedRimSeedPlacement(
        placement_id="p0",
        variant_id="v0",
        anchor=(1, 1),
        output_dir="E",
        seed_id="m0e",
        miner_cells=frozenset({(1, 1)}),
        extension_cells=frozenset({(0, 1)}),
        m_output_stub=(2, 1),
        throughput_factor=16,
        route_probe_path=((2, 1), (3, 1)),
    )
    return replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(placement,),
    )


def _artifacts(
    *,
    failed_layer: str | None = None,
    route_plan: Layer05RoutePlan | None = None,
    include_completed_layers: bool = True,
) -> GoldenSolverArtifacts:
    summaries = _layer_summaries_completed() if include_completed_layers else ()
    completed = tuple(record.layer_slug for record in summaries)
    core = CoreStackRunResult(
        stack_result=StackRunResult(
            status=(
                StackRunStatus.SUCCESS
                if failed_layer is None
                else StackRunStatus.TIMEOUT_FAIL_CLOSED
            ),
            completed_layer_slugs=completed,
            failed_layer_slug=failed_layer,
            diagnostic_snapshot=None,
        ),
        layer_summaries=summaries,
    )
    return GoldenSolverArtifacts(
        core_result=core,
        complete_map=_minimal_complete_map(),
        exterior_plan=_exterior_plan(),
        rim_result=_rim_with_placement(),
        inner_fill=None,
        route_plan=route_plan,
        layer_summaries=summaries,
    )


def test_golden_eval_deterministic_score() -> None:
    artifacts = _artifacts(route_plan=_valid_route_plan())
    oracle = _empty_oracle()
    assert evaluate_against_golden(artifacts, oracle) == evaluate_against_golden(artifacts, oracle)


def test_invalid_scores_below_valid() -> None:
    invalid = evaluate_against_golden(
        _artifacts(failed_layer=LAYER_05_TRANSPORT_ROUTING),
        _empty_oracle(),
    )
    valid = evaluate_against_golden(_artifacts(route_plan=_valid_route_plan()), _empty_oracle())
    assert not invalid.valid
    assert valid.valid
    assert invalid.score < valid.score


def test_eval_result_fields() -> None:
    result = evaluate_against_golden(_artifacts(route_plan=_valid_route_plan()), _empty_oracle())
    assert isinstance(result, GoldenEvalResult)
    assert isinstance(result.diagnostics, tuple)
    assert result.routed_throughput == 16 * 30


def test_route_island_roots_ignore_exterior_void_cells() -> None:
    void_cells = frozenset((x, y) for x in range(-5, 6) for y in range(-5, 6))
    artifacts = GoldenSolverArtifacts(
        core_result=CoreStackRunResult(
            stack_result=StackRunResult(
                status=StackRunStatus.SUCCESS,
                completed_layer_slugs=(),
                failed_layer_slug=None,
                diagnostic_snapshot=None,
            ),
            layer_summaries=(),
        ),
        complete_map=_minimal_complete_map(void_cells=void_cells),
        exterior_plan=_exterior_plan(),
        rim_result=None,
        inner_fill=None,
        route_plan=_valid_route_plan(),
        layer_summaries=(),
    )
    roots = _connectivity_roots(artifacts)
    assert roots != void_cells
    assert len(roots) < len(void_cells)
    assert (0, 0) in roots


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_eval_on_stack_smoke_artifacts() -> None:
    golden_copy = load_golden_copy().removesuffix("$")
    oracle = build_golden_oracle(decode_copy_string(golden_copy).root)
    artifacts = run_golden_solver(
        copy_text=load_empty_copy(),
        game_data_rules=load_game_data_rules(),
        genetic_sample_seeds=load_genetic_sample_seeds(),
        config=GoldenSolverConfig(budget_ms=60_000),
    )
    result = evaluate_against_golden(artifacts, oracle)
    assert isinstance(result, GoldenEvalResult)
    assert isinstance(result.diagnostics, tuple)
    assert result.miner_count == 76
    assert result.routed_throughput >= 30960.0
    assert not any(d.startswith("transport_kind_mismatch") for d in result.diagnostics)
    assert result.valid
