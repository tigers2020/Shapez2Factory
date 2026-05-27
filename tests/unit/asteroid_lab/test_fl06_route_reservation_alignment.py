"""FL-06 — output_stub vs commit-time route reservation alignment (diagnostic)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
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
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import (
    RttpSkeletonBuilder,
)
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)
from harness.investigation.commit_route_reservation_diagnostic import (
    CommitRouteReservationSnapshot,
    PreliminaryFl06Cause,
    build_fl06_question_report,
    snapshot_commit_reservation,
)
from harness.investigation.rttp_final_layout_assert_probe import (
    FinalLayoutAssertCode,
    diagnose_final_layout,
)
from tests.support.rttp_narrow_corridor_fixture import (
    NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
    build_narrow_corridor_optimization_input,
    candidate_by_id,
)


@pytest.fixture
def narrow_corridor_optimization_input() -> OptimizationInput:
    return build_narrow_corridor_optimization_input()


@pytest.fixture
def narrow_skeleton(narrow_corridor_optimization_input: OptimizationInput):
    return RttpSkeletonBuilder.build(
        narrow_corridor_optimization_input,
        config=RttpSkeletonConfig(),
    )


def _first_candidate(
    inp: OptimizationInput,
    skeleton,
) -> tuple[object, CommitRouteReservationSnapshot]:
    generation = generate_candidates(
        inp,
        skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    cand = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    goals = frozenset(probe_goal_coords(inp, skeleton))
    snap = snapshot_commit_reservation(
        cand,
        skeleton=skeleton,
        inp=inp,
        goals=goals,
        committed_occupied=frozenset(),
        committed_route_cells=frozenset(),
        committed_fixed_output_transport_cells=frozenset(),
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    return cand, snap


def test_snapshot_commit_reservation_exports_probe_start_and_stub_membership(
    narrow_corridor_optimization_input: OptimizationInput,
    narrow_skeleton,
) -> None:
    _, snap = _first_candidate(narrow_corridor_optimization_input, narrow_skeleton)
    assert isinstance(snap, CommitRouteReservationSnapshot)
    assert snap.output_stub is not None
    assert snap.probe_start is not None
    assert isinstance(snap.stub_in_path, bool)
    assert isinstance(snap.stub_in_route_cells, bool)
    assert snap.route_probe_start_policy is (
        RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED
    )


def test_fl06_question_report_fields(
    narrow_corridor_optimization_input: OptimizationInput,
    narrow_skeleton,
) -> None:
    _, snap = _first_candidate(narrow_corridor_optimization_input, narrow_skeleton)
    report = build_fl06_question_report(snap)
    assert report.q1_probe_start == snap.probe_start
    assert report.q2_probe_start_equals_output_stub == snap.probe_start_is_output_stub
    assert report.q3_path_contains_output_stub == snap.stub_in_path
    assert report.q4_route_cells_contains_output_stub == snap.stub_in_route_cells
    assert report.start_policy is RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED
    assert isinstance(report.preliminary_outcome, PreliminaryFl06Cause)


def test_narrow_corridor_single_commit_documents_q1_q4_relationship(
    narrow_corridor_optimization_input: OptimizationInput,
    narrow_skeleton,
) -> None:
    """Document Q1–Q4 on narrow corridor; single commit may not reproduce FL-06."""
    cand, snap = _first_candidate(narrow_corridor_optimization_input, narrow_skeleton)
    report = build_fl06_question_report(snap)
    if snap.probe_start_is_output_stub:
        assert report.q2_probe_start_equals_output_stub is True
    if snap.stub_in_path:
        assert report.q3_path_contains_output_stub is True
    if snap.stub_in_route_cells:
        assert report.q4_route_cells_contains_output_stub is True
        code, _ = diagnose_final_layout(
            (cand.candidate_id,),
            snap.route_cells,
            {cand.candidate_id: cand},
            narrow_corridor_optimization_input,
        )
        assert code is not FinalLayoutAssertCode.FL_06
        assert validate_final_layout(
            (cand.candidate_id,),
            snap.route_cells,
            {cand.candidate_id: cand},
            narrow_corridor_optimization_input,
        )


H1A_NARROW_CORRIDOR_CANDIDATE_ID = "7,5:cat_bv_1_N_ext0:shape_belt"


def test_incremental_commit_reserved_routes_include_output_stub_after_fallback(
    narrow_corridor_optimization_input: OptimizationInput,
    narrow_skeleton,
) -> None:
    """H1a: platform fallback omits stub from path; reservation must still include stub (FL-06)."""
    inp = narrow_corridor_optimization_input
    generation = generate_candidates(
        inp,
        narrow_skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    cand = candidate_by_id(generation, H1A_NARROW_CORRIDOR_CANDIDATE_ID)
    snap = snapshot_commit_reservation(
        cand,
        skeleton=narrow_skeleton,
        inp=inp,
        goals=frozenset(probe_goal_coords(inp, narrow_skeleton)),
        committed_occupied=frozenset(),
        committed_route_cells=frozenset(),
        committed_fixed_output_transport_cells=frozenset(),
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert snap.probe_start_is_output_stub is False
    assert snap.route_cells
    assert snap.stub_in_route_cells is False

    domain = initial_commit_domain(narrow_skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=(cand.candidate_id,)),
        {cand.candidate_id: cand},
        inp,
        narrow_skeleton,
        domain=domain,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    by_id = {cand.candidate_id: cand}
    assert cand.output_stub in result.reserved_route_cells
    code, detail = diagnose_final_layout(
        result.committed_ids,
        result.reserved_route_cells,
        by_id,
        inp,
    )
    assert code is FinalLayoutAssertCode.FL_OK, detail
    assert validate_final_layout(
        result.committed_ids,
        result.reserved_route_cells,
        by_id,
        inp,
    )


def test_output_stub_not_reserved_conflict_reason_exists() -> None:
    assert CommitConflictReason.OUTPUT_STUB_NOT_RESERVED.value == "output_stub_not_reserved"
