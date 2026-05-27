"""Gate A overlap graph packing bounds (P1-ELCP-RF-B1 Phase 0)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.input_contracts import RttpPipelineConfig
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.selection.primary_genome import select_primary_genome
from django_apps.asteroid_lab.reconstruction.complete_map import (
    build_reconstruction_complete_map,
)
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
from harness.investigation.rttp_overlap_graph_packing_bounds import (
    build_overlap_packing_bounds_report,
)
from tests.support.rttp_b1_gate_a_frozen_bounds import (
    GATE_A_BEST_KNOWN_IS,
    GATE_A_GREEDY_REGRET_BASELINE,
    GATE_A_PHASE0_VERDICT,
    GATE_A_TARGET_FLOOR,
    GATE_A_UPPER_BOUND,
    GATE_A_UPPER_BOUND_METHOD,
    GATE_A_VERTEX_COUNT,
)


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.django_db
@pytest.mark.slow
def test_recovery_map_overlap_packing_bounds_gate_a_parity_config(
    imported_game_data_batch_module: object,
) -> None:
    """Gate A Phase 0 bounds; prints report for frozen constants (P1-ELCP-RF-B1)."""
    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.management.commands.import_rttp_core_recovery_test_map import (
        import_core_recovery_test_map,
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
        boundary_run_id="elcp-rf-b1-phase0-bounds",
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
        run_rttp_pipeline(
            inp,
            policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
            fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
            route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
            pipeline_config=pipeline_config,
        )

    assert captured.get("genome") is not None
    report = build_overlap_packing_bounds_report(
        normal_candidates=captured["normal_candidates"],
        skeleton=captured["skeleton"],
        inp=captured["inp"],
        goal_count=captured["goal_count"],
    )

    assert report.vertex_count == GATE_A_VERTEX_COUNT
    assert report.greedy_regret_baseline == GATE_A_GREEDY_REGRET_BASELINE
    assert report.phase0_verdict == GATE_A_PHASE0_VERDICT
    assert report.best_known_independent_set_size == GATE_A_BEST_KNOWN_IS
    assert report.target_floor == GATE_A_TARGET_FLOOR
    assert report.upper_bound == GATE_A_UPPER_BOUND
    assert report.upper_bound_method == GATE_A_UPPER_BOUND_METHOD
    assert report.upper_bound_method in {
        "component_exact",
        "greedy_coloring",
        "mixed",
    }
    assert report.upper_bound >= report.best_known_independent_set_size
    assert report.best_known_independent_set_size > report.greedy_regret_baseline + 5

    print(f"B1_PHASE0_REPORT={report.to_dict()}")
    print(f"B1_PHASE0_VERDICT={report.phase0_verdict}")
