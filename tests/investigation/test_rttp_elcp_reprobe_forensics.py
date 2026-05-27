"""Integration: ELCP mirror forensics parity vs production incremental_commit."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from unittest.mock import patch

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.routing.exterior_lane_capacity_planner import (
    build_exterior_lane_capacity_plan,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
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
from harness.investigation.rttp_elcp_reprobe_forensics import (
    ElcpProbeFailureClass,
    assert_mirror_parity,
    build_deferred_retry_audit,
    build_elcp_primary_mirror_ledger,
    load_recovery_evidence_compare,
)
from harness.investigation.rttp_elcp_reprobe_step_forensics import extract_elcp_reprobe_forensics
from harness.investigation.rttp_elcp_universe_sanity import extract_elcp_attempt_universe_sanity

RECOVERY_SLUG = "rttp-core-recovery-test-map"

@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


@pytest.mark.django_db
def test_mirror_parity_matches_incremental_commit_on_elcp_plan(
    greenfield_optimization_input: OptimizationInput,
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    inp = greenfield_optimization_input
    plan = build_exterior_lane_capacity_plan(
        inp,
        max_asteroid_throughput_per_min=Decimal("5760"),
        transport_kind=inp.transport_kind,
    )
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = initial_commit_domain(skeleton, inp)
    genome = PlacementGenome(commit_order=())
    candidates_by_id: dict[str, object] = {}
    production = incremental_commit(
        genome,
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
        exterior_lane_plan=plan,
        resource_kind="shape",
    )
    mirror = build_elcp_primary_mirror_ledger(
        genome=genome,
        candidates_by_id=candidates_by_id,
        inp=inp,
        skeleton=skeleton,
        domain=domain,
        exterior_lane_plan=plan,
        route_probe_start_policy=RouteProbeStartPolicy.OUTPUT_STUB_ONLY,
        resource_kind="shape",
    )
    assert_mirror_parity(production=production, mirror=mirror)


@pytest.mark.django_db
@pytest.mark.slow
def test_recovery_map_primary_reprobe_mass_reproduced(
    imported_game_data_batch_module: object,
) -> None:
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
        boundary_run_id="elcp-rf-recovery-forensics",
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
    primary_results: list = []
    real_commit = incremental_commit

    def _capture_primary(*args: object, **kwargs: object):
        result = real_commit(*args, **kwargs)
        primary_results.append(result)
        captured["genome"] = args[0]
        captured["candidates_by_id"] = args[1]
        captured["inp"] = args[2]
        captured["skeleton"] = args[3]
        captured["domain"] = kwargs["domain"]
        captured["exterior_lane_plan"] = kwargs.get("exterior_lane_plan")
        captured["route_probe_start_policy"] = kwargs.get("route_probe_start_policy")
        captured["resource_kind"] = kwargs.get("resource_kind")
        return result

    with patch(
        "django_apps.asteroid_lab.optimization.pipeline.incremental_commit",
        side_effect=_capture_primary,
    ):
        pipeline_result = run_rttp_pipeline(
            inp,
            policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
            fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
            route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
            pipeline_config=pipeline_config,
        )

    assert primary_results, "primary incremental_commit was not called"
    primary = primary_results[0]
    assert captured.get("exterior_lane_plan") is not None, "ELCP plan required for RF.1"
    reprobe_count = sum(
        1
        for conflict in primary.conflicts
        if conflict.reason is CommitConflictReason.REPROBE_FAILED
    )
    assert reprobe_count > 0, "expected primary REPROBE_FAILED mass on recovery map"

    plan = captured["exterior_lane_plan"]
    assert plan is not None
    mirror = build_elcp_primary_mirror_ledger(
        genome=captured["genome"],
        candidates_by_id=captured["candidates_by_id"],
        inp=captured["inp"],
        skeleton=captured["skeleton"],
        domain=captured["domain"],
        exterior_lane_plan=plan,
        route_probe_start_policy=captured["route_probe_start_policy"],
        resource_kind=str(captured["resource_kind"]),
    )
    assert_mirror_parity(production=primary, mirror=mirror)

    failed = mirror.ledger
    assert failed, "ledger should contain failed attempts"
    known = sum(
        1
        for row in failed
        if row.probe_failure_class is not ElcpProbeFailureClass.UNKNOWN_REPROBE_FAILED
    )
    coverage = known / len(failed)
    assert coverage >= 0.95, f"bucket coverage {coverage:.2%} below 95%"

    audit = build_deferred_retry_audit(
        primary_commit_result=primary,
        commit_order=tuple(captured["genome"].commit_order),
        candidates_by_id=captured["candidates_by_id"],
        inp=captured["inp"],
        ledger=failed,
    )
    assert audit["primary_reprobe_failed_count"] == reprobe_count

    universe = extract_elcp_attempt_universe_sanity(
        algorithm_steps=pipeline_result.algorithm_steps,
        inp=inp,
        pipeline_config=pipeline_config,
        primary_commit_result=primary,
        exterior_lane_plan=captured.get("exterior_lane_plan"),
    )
    assert universe["commit_order_len"] == len(mirror.ledger) + len(primary.committed_ids)
    assert universe["normal_candidate_count"] > universe["commit_order_len"], (
        "forensics universe must be narrower than full normal candidate pool"
    )

    step_forensics = extract_elcp_reprobe_forensics(pipeline_result.algorithm_steps)
    assert step_forensics["conflict_count"] == len(primary.conflicts)
    assert (
        step_forensics["lane_capacity_shortfall_count"]
        == primary.lane_capacity_shortfall_count
    )
    assert (
        step_forensics["route_feasible_shortfall_count"]
        == primary.route_feasible_shortfall_count
    )

    histogram = Counter(row.probe_failure_class.value for row in failed)
    print(f"ELCP_RF_PRIMARY_COMMITTED={len(primary.committed_ids)}")
    print(f"ELCP_RF_REPROBE_CONFLICTS={reprobe_count}")
    print(f"ELCP_RF_BUCKET_COVERAGE={coverage:.4f}")
    print(f"ELCP_RF_BUCKET_HISTOGRAM={dict(histogram)}")
    print(f"ELCP_RF_DEFERRED_AUDIT={audit}")
    print(f"ELCP_RF_UNIVERSE_SANITY={universe}")


def test_load_recovery_evidence_compare_reads_file_when_present() -> None:
    result = load_recovery_evidence_compare(primary_committed_count=3)
    assert "loaded" in result
