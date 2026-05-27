"""Task A5 — output stub reservation outside traversable envelope (FL-06 hardening)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    RttpPipelineConfig,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import (
    RttpSkeletonBuilder,
)
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)
from django_apps.asteroid_lab.reconstruction.complete_map import (
    build_reconstruction_complete_map,
)
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cell_count_for_placement,
)
from django_apps.asteroid_lab.services.placement_goal import compute_placement_goal_count
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
)
from django_apps.asteroid_lab.services.throughput_target import (
    compute_target_throughput_per_min,
    parse_throughput_target_percent,
    primary_reconstruction_max_per_min,
)
from tests.support.rttp_core_recovery_test_map_expectations import (
    expected_placement_metrics_for_complete_map,
)


@pytest.mark.django_db
def test_outward_rim_stub_outside_mineable_is_reserved_on_recovery_map(
    imported_game_data_batch_module: object,
) -> None:
    """Regression: blocked non-mineable output_stub must still enter reserved_route_cells."""

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
        boundary_run_id="a5-stub-reservation",
    )
    complete_map = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    inp = optimization_input_from_reconstruction(
        recon,
        cleanup=cleanup,
        catalog_slice=build.catalog_slice,
        complete_map=complete_map,
    )
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    candidate = next(c for c in generation.normal_candidates if c.reachable)
    assert candidate.output_stub not in inp.mineable_cells

    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=(candidate.candidate_id,)),
        {candidate.candidate_id: candidate},
        inp,
        skeleton,
        domain=domain,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert candidate.candidate_id in result.committed_ids
    assert candidate.output_stub in result.reserved_route_cells
    assert not any(
        c.reason == CommitConflictReason.OUTPUT_STUB_NOT_RESERVED for c in result.conflicts
    )
    assert validate_final_layout(
        result.committed_ids,
        result.reserved_route_cells,
        {candidate.candidate_id: candidate},
        inp,
    )


@pytest.mark.django_db
def test_recovery_pipeline_commit_count_not_below_after_a4_baseline(
    imported_game_data_batch_module: object,
) -> None:
    """Pipeline commits some extractors but stays below map-derived placement_goal_count."""

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
        boundary_run_id="a5-pipeline",
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
    expected_platform, expected_goal = expected_placement_metrics_for_complete_map(
        complete_map,
        inp.transport_kind,
        placement_target_percent=percent,
    )
    assert platform == expected_platform
    assert expected_goal == compute_placement_goal_count(
        asteroid_field_cell_count=platform,
        placement_target_percent=percent,
    )
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
    committed = len(pipeline_result.commit_result.committed_ids)
    stub_conflicts = sum(
        1
        for c in pipeline_result.commit_result.conflicts
        if c.reason == CommitConflictReason.OUTPUT_STUB_NOT_RESERVED
    )
    plan = pipeline_result.placement_goal_plan
    assert plan is not None
    assert plan.placement_goal_count == expected_goal
    assert plan.asteroid_field_cell_count == expected_platform
    assert 0 < committed < expected_goal
    assert stub_conflicts < 38
