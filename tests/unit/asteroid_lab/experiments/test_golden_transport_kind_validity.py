"""PR-10: transport kind normalization for golden hard-validity."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_eval import (
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
from shapez2_factory.application.asteroid_lab.experiments.golden_valid_baseline import (
    assert_master_valid_eval_result,
)
from shapez2_factory.application.asteroid_lab.experiments.transport_kind_normalization import (
    format_transport_kind_mismatch_diagnostic,
    normalize_transport_family,
    transport_families_compatible,
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
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    TransportKind,
)
from shapez2_factory.application.asteroid_lab.stack_runner import CoreStackRunResult
from shapez2_factory.domain.asteroid_lab.coord_frames import CoordFrame
from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string
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
        extractor_anchors_direct=frozenset(),
        extractor_anchors_normalized=frozenset(),
        extension_cells=frozenset(),
        belt_edges=frozenset(),
        layout_miner_count=0,
        layout_extension_count=0,
        belt_count=0,
        entry_count=0,
        bbox=(0, 0, 0, 0),
    )


def test_normalize_transport_family_aliases() -> None:
    assert normalize_transport_family("shape") == "shape"
    assert normalize_transport_family("space_belt") == "shape"
    assert normalize_transport_family(TransportKind.SHAPE_BELT) == "shape"
    assert normalize_transport_family("fluid") == "fluid"
    assert normalize_transport_family("space_pipe") == "fluid"
    assert normalize_transport_family(TransportKind.FLUID_PIPE) == "fluid"
    assert normalize_transport_family("unknown") is None


@pytest.mark.parametrize(
    ("exterior_kind", "route_kind", "expected"),
    [
        ("shape", "space_belt", True),
        ("fluid", "space_pipe", True),
        ("shape", "space_pipe", False),
        ("fluid", "space_belt", False),
    ],
)
def test_transport_families_compatible_matrix(
    exterior_kind: str,
    route_kind: str,
    expected: bool,
) -> None:
    assert (
        transport_families_compatible(
            exterior_transport_kind=exterior_kind,
            route_transport_kind=route_kind,
        )
        is expected
    )


def test_mismatch_diagnostic_includes_raw_and_normalized_values() -> None:
    line = format_transport_kind_mismatch_diagnostic(
        exterior_transport_kind="shape",
        route_transport_kind="space_pipe",
    )
    assert line.startswith("transport_kind_mismatch:")
    assert "exterior=shape" in line
    assert "route=space_pipe" in line
    assert "exterior_family=shape" in line
    assert "route_family=fluid" in line


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


def _exterior_plan(*, transport_kind: str) -> ExteriorConnectionPlan:
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
        transport_kind=transport_kind,
        terrain_upper_bound_per_min=Decimal("1000"),
        planning_target_per_min=Decimal("800"),
        per_connector_capacity_per_min=Decimal("100"),
        required_connector_count=1,
        reference_connector_count=1,
        spare_connector_count=0,
        planned_connectors=(connector,),
        unmet_reason=None,
    )


def _route_plan(*, transport_kind: str) -> Layer05RoutePlan:
    resource_kind = "fluid" if transport_kind == "space_pipe" else "shape"
    return Layer05RoutePlan(
        version="layer05_route_plan_v1",
        resource_kind=resource_kind,
        transport_kind=transport_kind,
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
                transport_kind=transport_kind,
                connector_ids=frozenset({"c0"}),
                member_placement_ids=frozenset({"p0"}),
                route_cells=frozenset({(1, 1), (2, 1)}),
                used_m=1,
                capacity_m=12,
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


def _artifacts(
    *,
    exterior_kind: str,
    route_kind: str,
) -> GoldenSolverArtifacts:
    placement = CommittedRimSeedPlacement(
        placement_id="p0",
        variant_id="v0",
        anchor=(1, 1),
        output_dir="E",
        seed_id="m0e",
        miner_cells=frozenset({(1, 1)}),
        extension_cells=frozenset(),
        m_output_stub=(2, 1),
        throughput_factor=16,
        route_probe_path=(),
    )
    summaries = _layer_summaries_completed()
    core = CoreStackRunResult(
        stack_result=StackRunResult(
            status=StackRunStatus.SUCCESS,
            completed_layer_slugs=tuple(record.layer_slug for record in summaries),
            failed_layer_slug=None,
            diagnostic_snapshot=None,
        ),
        layer_summaries=summaries,
    )
    return GoldenSolverArtifacts(
        core_result=core,
        complete_map=ReconstructionCompleteMap(
            cells=(),
            field_cells=frozenset(),
            shape_field_cell_count=0,
            fluid_field_cell_count=0,
            external_void_cells=frozenset(),
            coord_frame=CoordFrame.ISLAND_RAW,
        ),
        exterior_plan=_exterior_plan(transport_kind=exterior_kind),
        rim_result=replace(
            build_empty_integrated_rim_greedy_result(),
            committed_placements=(placement,),
        ),
        inner_fill=None,
        route_plan=_route_plan(transport_kind=route_kind),
        layer_summaries=summaries,
    )


@pytest.mark.parametrize(
    ("exterior_kind", "route_kind"),
    [
        ("shape", "space_belt"),
        ("fluid", "space_pipe"),
    ],
)
def test_compatible_transport_kinds_are_valid(
    exterior_kind: str,
    route_kind: str,
) -> None:
    result = evaluate_against_golden(
        _artifacts(exterior_kind=exterior_kind, route_kind=route_kind),
        _empty_oracle(),
    )
    assert result.valid
    assert not any(d.startswith("transport_kind_mismatch") for d in result.diagnostics)


@pytest.mark.parametrize(
    ("exterior_kind", "route_kind"),
    [
        ("shape", "space_pipe"),
        ("fluid", "space_belt"),
    ],
)
def test_incompatible_transport_kinds_are_invalid(
    exterior_kind: str,
    route_kind: str,
) -> None:
    result = evaluate_against_golden(
        _artifacts(exterior_kind=exterior_kind, route_kind=route_kind),
        _empty_oracle(),
    )
    assert not result.valid
    assert any(
        d.startswith("transport_kind_mismatch:")
        and f"exterior={exterior_kind}" in d
        and f"route={route_kind}" in d
        for d in result.diagnostics
    )


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_golden_stack_smoke_valid_after_transport_kind_normalization() -> None:
    oracle = build_golden_oracle(decode_copy_string(load_golden_copy()).root)
    artifacts = run_golden_solver(
        copy_text=load_empty_copy(),
        game_data_rules=load_game_data_rules(),
        genetic_sample_seeds=load_genetic_sample_seeds(),
        config=GoldenSolverConfig(budget_ms=60_000),
    )
    result = evaluate_against_golden(artifacts, oracle)
    assert_master_valid_eval_result(result)
