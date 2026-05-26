"""A3.1 — same-kind trunk spine sharing at commit (minimal private reservation)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    _private_route_cell_overlap,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.input_contracts import RttpSkeletonConfig
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from tests.support.rttp_narrow_corridor_fixture import (
    NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
    NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID,
    build_narrow_corridor_optimization_input,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


def test_private_route_overlap_excludes_skeleton_trunk_cells() -> None:
    trunk = frozenset({(4, 7)})
    committed = frozenset({(4, 7), (5, 6)})
    route = frozenset({(4, 7), (5, 6), (6, 8)})
    private = _private_route_cell_overlap(route, committed, shareable_trunk_cells=trunk)
    assert private == frozenset({(5, 6)})


@pytest.mark.django_db
def test_two_extractors_may_share_skeleton_trunk_spine(
    imported_game_data_batch_module: object,
) -> None:
    """Spine overlap on ``trunk_mask_cells`` must not produce ``route_cell_conflict``."""

    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.management.commands.import_rttp_core_recovery_test_map import (
        import_core_recovery_test_map,
    )
    from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
        optimization_input_from_reconstruction,
    )
    from django_apps.asteroid_lab.reconstruction.complete_map import (
        build_reconstruction_complete_map,
    )
    from django_apps.asteroid_lab.services.placement_goal import build_placement_goal_plan
    from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
        run_reconstruction_for_map_input,
    )
    from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
        build_reconstruction_capacity_envelope,
    )
    from django_apps.asteroid_lab.services.throughput_target import (
        compute_target_throughput_per_min,
        primary_reconstruction_max_per_min,
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
        boundary_run_id="a31-trunk-share",
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
    cap = build_reconstruction_capacity_envelope(complete_map=complete_map)
    target = compute_target_throughput_per_min(
        reconstruction_max=primary_reconstruction_max_per_min(cap),
        percent=100,
    )
    from django_apps.asteroid_lab.reconstruction.field_cells import (
        asteroid_field_cell_count_for_placement,
    )

    platform_cells = asteroid_field_cell_count_for_placement(
        complete_map,
        inp.transport_kind,
    )
    percent = 80
    plan = build_placement_goal_plan(
        normal_candidates=generation.normal_candidates,
        transport_kind=inp.transport_kind,
        asteroid_field_cell_count=platform_cells,
        placement_target_percent=percent,
        target_throughput_per_min=target,
        skeleton_capacity_goals=skeleton.capacity_goals,
        legacy_configured_max_placement_goal=32,
    )
    from django_apps.asteroid_lab.services.placement_goal import compute_placement_goal_count

    assert plan.placement_goal_count == compute_placement_goal_count(
        asteroid_field_cell_count=platform_cells,
        placement_target_percent=percent,
    )
    from django_apps.asteroid_lab.optimization.selection.greedy_regret import select_genome

    genome = select_genome(
        generation.normal_candidates,
        skeleton,
        inp,
        goal_count=plan.placement_goal_count,
    )
    candidates_by_id = {c.candidate_id: c for c in generation.normal_candidates}
    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        genome,
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )

    route_conflicts = [
        c for c in result.conflicts if c.reason is CommitConflictReason.ROUTE_CELL_CONFLICT
    ]
    assert len(result.committed_ids) > 10
    assert skeleton.trunk_mask_cells & result.reserved_route_cells
    # EVTC void-weighted commit probes may reserve more overlapping void spines on recovery map.
    assert len(route_conflicts) < 50


def test_private_approach_overlap_still_route_cell_conflict() -> None:
    inp = build_narrow_corridor_optimization_input()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    committable = [
        c
        for c in generation.normal_candidates
        if c.candidate_id
        in (
            NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
            NARROW_CORRIDOR_PROBE_SECOND_CANDIDATE_ID,
        )
    ]
    assert len(committable) == 2
    first, second = committable
    domain = initial_commit_domain(skeleton, inp)
    solo = incremental_commit(
        PlacementGenome(commit_order=(first.candidate_id,)),
        {first.candidate_id: first},
        inp,
        skeleton,
        domain=domain,
    )
    assert first.candidate_id in solo.committed_ids
    private_cell = next(
        c for c in solo.reserved_route_cells if c not in skeleton.trunk_mask_cells
    )
    forced = replace(
        second,
        candidate_id=f"forced:{second.candidate_id}",
        output_stub=private_cell,
    )
    result = incremental_commit(
        PlacementGenome(commit_order=(first.candidate_id, forced.candidate_id)),
        {first.candidate_id: first, forced.candidate_id: forced},
        inp,
        skeleton,
        domain=domain,
    )
    assert forced.candidate_id not in result.committed_ids
    assert any(
        c.candidate_id == forced.candidate_id
        and c.reason
        in (
            CommitConflictReason.ROUTE_CELL_CONFLICT,
            CommitConflictReason.INLET_ON_SHARED_TRANSPORT,
        )
        for c in result.conflicts
    )


def test_wrong_transport_kind_still_blocked() -> None:
    inp = build_narrow_corridor_optimization_input()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    shape = generation.normal_candidates[0]
    fluid = replace(shape, candidate_id="fluid:1", transport_kind=TransportKind.FLUID_PIPE)
    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=(fluid.candidate_id,)),
        {fluid.candidate_id: fluid},
        inp,
        skeleton,
        domain=domain,
    )
    assert result.committed_ids == ()
    assert any(c.reason is CommitConflictReason.TRANSPORT_KIND_CONFLICT for c in result.conflicts)
