"""PR-2: outward rim attach surface + platform route probe start fallback."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    CandidateRejectReason,
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.candidates.transport_attach_surface import (
    outward_dirs,
    transport_attach_surface_cells,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    build_route_domain_from_skeleton,
)
from django_apps.asteroid_lab.optimization.routing.route_probe_start import (
    resolve_route_probe_start,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from tests.support.catalog_test_fixtures import build_minimal_test_catalog_slice
from tests.support.rttp_narrow_corridor_fixture import (
    NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
    build_narrow_corridor_optimization_input,
    candidate_by_id,
)
from tests.unit.asteroid_lab.conftest import (
    _external_margin_goals,
    _external_void_ring,
    _perimeter_cells,
)


def test_route_probe_start_policy_enum() -> None:
    assert (
        RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED.value
        == "platform_fallback_when_stub_blocked"
    )


def test_reject_reason_attach_surface_exists() -> None:
    assert (
        CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_NOT_ON_ATTACH_SURFACE.value
        == "fixed_output_transport_not_on_attach_surface"
    )


def test_reject_reason_probe_start_blocked_exists() -> None:
    assert CandidateRejectReason.ROUTE_PROBE_START_BLOCKED.value == "route_probe_start_blocked"


@pytest.fixture
def narrow_corridor_optimization_input() -> OptimizationInput:
    return build_narrow_corridor_optimization_input()


@pytest.fixture
def narrow_skeleton(narrow_corridor_optimization_input: OptimizationInput):
    return RttpSkeletonBuilder.build(
        narrow_corridor_optimization_input,
        config=RttpSkeletonConfig(),
    )


def _west_rim_greenfield() -> OptimizationInput:
    mineable = frozenset((x, y) for x in range(5, 9) for y in range(5, 9))
    rim = frozenset({(5, 5)})
    inner = mineable - rim
    external_void = _external_void_ring(mineable)
    return OptimizationInput(
        mineable_cells=mineable,
        rim_cells=rim,
        inner_cells=inner,
        external_void_cells=external_void,
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=frozenset(),
        transport_kind=TransportKind.SHAPE_BELT,
        route_goals=_external_margin_goals(_perimeter_cells(mineable), external_void),
        existing_transport_cells=frozenset(),
        catalog_slice=build_minimal_test_catalog_slice(),
    )


def test_platform_fallback_when_stub_in_void(
    narrow_corridor_optimization_input: OptimizationInput,
    narrow_skeleton,
) -> None:
    inp = narrow_corridor_optimization_input
    domain = build_route_domain_from_skeleton(narrow_skeleton, inp)
    generation = generate_candidates(
        inp,
        narrow_skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    cand = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    start = resolve_route_probe_start(
        anchor_coord=cand.anchor_coord,
        output_stub=cand.output_stub,
        domain=domain,
        policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert start == cand.route_probe_start
    assert start is not None
    assert start in {cand.anchor_coord, cand.output_stub}
    if cand.output_stub in domain.blocked_cells:
        assert start == cand.anchor_coord


def test_outward_fot_on_external_void_not_mineable(
    narrow_corridor_optimization_input: OptimizationInput,
    narrow_skeleton,
) -> None:
    inp = narrow_corridor_optimization_input
    generation = generate_candidates(
        inp,
        narrow_skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    cand = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    fot = fixed_output_transport_cell(cand)
    assert fot in inp.external_void_cells
    assert fot not in inp.mineable_cells


def test_outward_rejects_inward_rim_rotation() -> None:
    inp = _west_rim_greenfield()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.RIM_ONLY,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    inward = [r for r in result.rejected_candidates if "cat_bv_1_E" in r.candidate_id]
    assert inward
    assert any(
        r.rejection_reason
        in (
            CandidateRejectReason.OUTPUT_DIR_NOT_OUTWARD_FROM_RIM,
            CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE,
        )
        for r in inward
    )


def test_narrow_corridor_has_normal_under_outward_policy(
    narrow_corridor_optimization_input: OptimizationInput,
    narrow_skeleton,
) -> None:
    result = generate_candidates(
        narrow_corridor_optimization_input,
        narrow_skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert len(result.normal_candidates) >= 1


def test_resolve_route_probe_start_matches_commit_reprobe(
    narrow_corridor_optimization_input: OptimizationInput,
    narrow_skeleton,
) -> None:
    inp = narrow_corridor_optimization_input
    generation = generate_candidates(
        inp,
        narrow_skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTWARD_FROM_RIM,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    cand = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    domain = initial_commit_domain(narrow_skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=(cand.candidate_id,)),
        {cand.candidate_id: cand},
        inp,
        narrow_skeleton,
        domain=domain,
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert cand.candidate_id in result.committed_ids


def test_transport_attach_surface_is_void_union_ring(
    narrow_corridor_optimization_input: OptimizationInput,
    narrow_skeleton,
) -> None:
    attach = transport_attach_surface_cells(
        narrow_corridor_optimization_input,
        narrow_skeleton,
    )
    assert narrow_corridor_optimization_input.external_void_cells <= attach
    assert narrow_skeleton.ring_cells <= attach


def test_outward_dirs_prefers_catalog_output_dir_on_rim(
    narrow_corridor_optimization_input: OptimizationInput,
    narrow_skeleton,
) -> None:
    inp = narrow_corridor_optimization_input
    domain = build_route_domain_from_skeleton(narrow_skeleton, inp)
    anchor = (7, 5)
    dirs = outward_dirs(
        anchor,
        "S",
        inp=inp,
        skeleton=narrow_skeleton,
        domain=domain,
    )
    assert dirs == frozenset({"S"})
