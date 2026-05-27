"""Synthetic parity: greedy-regret selection trace vs production select_genome."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from unittest.mock import patch

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
    RttpSkeletonConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    SelectionConfig,
    select_genome,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cell_count_for_placement,
)
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
)
from django_apps.asteroid_lab.services.throughput_target import (
    compute_target_throughput_per_min,
    parse_throughput_target_percent,
    primary_reconstruction_max_per_min,
)
from harness.investigation.rttp_elcp_universe_sanity import extract_elcp_attempt_universe_sanity
from harness.investigation.rttp_greedy_regret_selection_trace import (
    SelectionStopReason,
    assert_selection_trace_parity,
    attrition_class_coverage,
    trace_greedy_regret_selection,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


def _pattern_by_id(pattern_id: str):
    for pattern in build_pattern_library():
        if pattern.pattern_id == pattern_id:
            return pattern
    msg = f"pattern not found: {pattern_id!r}"
    raise AssertionError(msg)


def _translate(anchor: tuple[int, int], offset: tuple[int, int]) -> tuple[int, int]:
    return (anchor[0] + offset[0], anchor[1] + offset[1])


def _bundle_candidate(
    anchor: tuple[int, int],
    *,
    pattern_id: str = "lin_e_len0",
    throughput_factor: int | None = None,
    route_probe_cost: int = 5,
) -> BundleCandidate:
    pattern = _pattern_by_id(pattern_id)
    occupied = frozenset(_translate(anchor, offset) for offset in pattern.occupied_offsets)
    output_stub = _translate(anchor, pattern.output_stub_offset)
    throughput = throughput_factor if throughput_factor is not None else pattern.throughput_factor
    return BundleCandidate(
        candidate_id=f"{anchor[0]},{anchor[1]}:{pattern.pattern_id}:shape_belt",
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=output_stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=throughput,
        route_probe_cost=route_probe_cost,
        reachable=True,
    )


def _skeleton_with_goals(
    greenfield_optimization_input: OptimizationInput,
    capacity_goals: int,
):
    skeleton = RttpSkeletonBuilder.build(
        greenfield_optimization_input,
        config=RttpSkeletonConfig(),
    )
    return replace(skeleton, capacity_goals=capacity_goals)


def test_trace_matches_select_genome_on_tiny_pool(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    skeleton = _skeleton_with_goals(inp, capacity_goals=4)
    config = SelectionConfig(lambda_regret=0.0)

    candidates = (
        _bundle_candidate((5, 5), throughput_factor=4, route_probe_cost=20),
        _bundle_candidate((8, 8), throughput_factor=16, route_probe_cost=1),
        _bundle_candidate((5, 8), throughput_factor=12, route_probe_cost=2),
        _bundle_candidate((8, 5), throughput_factor=8, route_probe_cost=3),
        _bundle_candidate((6, 5), throughput_factor=4, route_probe_cost=4),
        _bundle_candidate((5, 5), pattern_id="lin_n_len0", route_probe_cost=5),
    )

    production = select_genome(candidates, skeleton, inp, config=config)
    trace = trace_greedy_regret_selection(candidates, skeleton, inp, config=config)

    assert_selection_trace_parity(production=production, trace=trace)
    assert trace.commit_order == production.commit_order

    if trace.stop_reason is SelectionStopReason.POOL_EXHAUSTED:
        assert len(trace.round_trace) == len(trace.commit_order)
    else:
        assert len(trace.round_trace) == trace.resolved_goal

    assert attrition_class_coverage(trace) >= 0.95


@pytest.mark.django_db
@pytest.mark.slow
def test_recovery_map_selection_attrition_trace_gate_a_parity_config(
    imported_game_data_batch_module: object,
) -> None:
    """Gate A greedy-regret attrition trace vs production selection on recovery map.

    These constants are valid only for rttp-core-recovery-test-map under Gate A parity
    config (P1-ELCP-RF RF.1).
    """
    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.management.commands.import_rttp_core_recovery_test_map import (
        import_core_recovery_test_map,
    )
    from django_apps.asteroid_lab.optimization.selection.primary_genome import (
        select_primary_genome,
    )
    from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
        run_reconstruction_for_map_input,
    )
    from django_apps.web.services.asteroid_game_data_snapshot import (
        build_asteroid_game_data_snapshot_with_provenance,
    )

    _ = imported_game_data_batch_module
    project_id = import_core_recovery_test_map(replace=True)
    build = build_asteroid_game_data_snapshot_with_provenance()
    inp_row = m.AsteroidMapInput.objects.filter(project_id=project_id).first()
    assert inp_row is not None
    cleanup, recon = run_reconstruction_for_map_input(
        int(inp_row.pk),
        boundary_run_id="elcp-rf-a2-selection-attrition",
    )
    complete_map = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    inp = optimization_input_from_reconstruction(
        recon,
        cleanup=cleanup,
        catalog_slice=build.catalog_slice,
        complete_map=complete_map,
    )
    cap = build_reconstruction_capacity_envelope(complete_map=complete_map)
    percent = parse_throughput_target_percent({})
    target = compute_target_throughput_per_min(
        reconstruction_max=primary_reconstruction_max_per_min(cap),
        percent=percent,
    )
    platform = asteroid_field_cell_count_for_placement(complete_map, inp.transport_kind)
    pipeline_config = RttpPipelineConfig(
        target_throughput_per_min=target,
        placement_target_percent=percent,
        placement_platform_cell_count=platform,
        reconstruction_max_throughput_per_min=primary_reconstruction_max_per_min(cap),
    )

    captured: dict[str, object] = {}
    real_select = select_primary_genome

    def _capture_select(*args: object, **kwargs: object) -> PlacementGenome:
        captured["normal_candidates"] = tuple(kwargs["normal_candidates"])
        captured["goal_count"] = kwargs["goal_count"]
        captured["skeleton"] = kwargs["skeleton"]
        captured["inp"] = kwargs["inp"]
        genome = real_select(*args, **kwargs)
        captured["genome"] = genome
        return genome

    with patch(
        "django_apps.asteroid_lab.optimization.pipeline.select_primary_genome",
        side_effect=_capture_select,
    ):
        pipeline_result = run_rttp_pipeline(
            inp,
            policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
            fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
            route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
            pipeline_config=pipeline_config,
        )

    assert captured.get("genome") is not None, "select_primary_genome was not called"
    production_genome = captured["genome"]
    assert isinstance(production_genome, PlacementGenome)

    trace = trace_greedy_regret_selection(
        normal_candidates=captured["normal_candidates"],
        skeleton=captured["skeleton"],
        inp=captured["inp"],
        goal_count=captured["goal_count"],
    )
    assert_selection_trace_parity(production=production_genome, trace=trace)

    # Gate A only: rttp-core-recovery-test-map + RF.1 pipeline_config
    assert trace.normal_candidate_count == 356
    assert len(trace.commit_order) == 59
    assert trace.resolved_goal == 467
    # H1 evidence: stop_reason from trace outcome (baseline POOL_EXHAUSTED; not report prose)
    assert trace.stop_reason is SelectionStopReason.POOL_EXHAUSTED
    assert attrition_class_coverage(trace) >= 0.95

    universe = extract_elcp_attempt_universe_sanity(
        algorithm_steps=pipeline_result.algorithm_steps,
        inp=inp,
        pipeline_config=pipeline_config,
    )
    assert universe["candidate_pool_total"] == 9328
    assert universe["commit_order_len"] == len(trace.commit_order)
    assert universe["placement_goal_count"] == trace.resolved_goal

    histogram = Counter(row.attrition_class.value for row in trace.attrition_ledger)
    print(f"A2_ROUND_TRACE_LEN={len(trace.round_trace)}")
    print(f"A2_ATTRITION_HISTOGRAM={dict(histogram)}")
    print(f"A2_STOP_REASON={trace.stop_reason.value}")
