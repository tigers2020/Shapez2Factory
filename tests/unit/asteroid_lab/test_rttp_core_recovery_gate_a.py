"""Task A6 — Gate A primary slug validation + transport invariants (integration)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.rttp_layout_issue_codes import (
    ISSUE_CODE_MISSING_EXTERIOR_ROUTE,
    ISSUE_CODE_MISSING_OUTPUT_TRANSPORT,
)
from django_apps.asteroid_lab.contracts.rttp_recovery_evidence import (
    GATE_A_PRIMARY_SLUGS,
    RTTP_CORE_RECOVERY_TEST_MAP_SLUG,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    RttpPipelineConfig,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cell_count_for_placement,
)
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
)
from django_apps.asteroid_lab.services.rttp_route_connectivity import (
    count_exterior_connected_route_cells,
)
from django_apps.asteroid_lab.services.throughput_target import (
    compute_target_throughput_per_min,
    parse_throughput_target_percent,
    primary_reconstruction_max_per_min,
)


@pytest.mark.django_db
def test_recovery_map_validation_passes_with_placement_goal_shortfall_only(
    imported_game_data_batch_module: object,
) -> None:
    """62 < 467 is product shortfall; transport/exterior invariants must still pass validation."""

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
        boundary_run_id="a6-gate-a-validation",
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
    pipeline_result = run_rttp_pipeline(
        inp,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
        pipeline_config=RttpPipelineConfig(
            target_throughput_per_min=target,
            placement_target_percent=percent,
            placement_platform_cell_count=platform,
        ),
    )
    committed_count = len(pipeline_result.commit_result.committed_ids)
    plan = pipeline_result.placement_goal_plan
    assert plan is not None
    assert plan.placement_goal_count == 467
    assert committed_count > 0
    assert committed_count < plan.placement_goal_count
    assert pipeline_result.validation_passed is True

    commit_step = next(
        row
        for row in pipeline_result.algorithm_steps
        if row["step_id"] == RttpAlgorithmStepId.RTTP_COMMIT.value
    )
    layout_codes = list(commit_step["metrics"].get("layout_connectivity_issue_codes") or [])
    assert ISSUE_CODE_MISSING_OUTPUT_TRANSPORT not in layout_codes
    assert ISSUE_CODE_MISSING_EXTERIOR_ROUTE not in layout_codes

    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    exterior = count_exterior_connected_route_cells(
        pipeline_result.commit_result.reserved_route_cells,
        skeleton.trunk_mask_cells,
    )
    assert exterior > 0
    assert len(pipeline_result.commit_result.reserved_route_cells) > 0


def test_gate_a_primary_slugs_frozen_set_includes_recovery_map() -> None:
    assert RTTP_CORE_RECOVERY_TEST_MAP_SLUG in GATE_A_PRIMARY_SLUGS
