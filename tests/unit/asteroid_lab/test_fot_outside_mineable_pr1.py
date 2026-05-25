"""PR-1: FOT must not lie on mineable_cells (INV-FOT-01)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    CandidateRejectReason,
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)
from tests.support.rttp_narrow_corridor_fixture import (
    build_narrow_corridor_optimization_input,
)
from tests.unit.asteroid_lab.conftest import (
    _external_margin_goals,
    _external_void_ring,
    _perimeter_cells,
)


def test_fixed_output_transport_policy_enum_values() -> None:
    assert FixedOutputTransportPolicy.ALLOW.value == "allow"
    assert FixedOutputTransportPolicy.OUTSIDE_MINEABLE.value == "outside_mineable"
    assert FixedOutputTransportPolicy.OUTWARD_FROM_RIM.value == "outward_from_rim"


def test_candidate_reject_reason_fot_inside_mineable_exists() -> None:
    assert (
        CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE.value
        == "fixed_output_transport_inside_mineable"
    )


def test_candidate_reject_reason_fot_kind_blocked_exists() -> None:
    assert (
        CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_KIND_BLOCKED.value
        == "fixed_output_transport_kind_blocked"
    )


@pytest.fixture
def narrow_corridor_optimization_input() -> OptimizationInput:
    return build_narrow_corridor_optimization_input()


def _west_rim_greenfield() -> OptimizationInput:
    """4×4 mineable block; single west-rim anchor (5,5) for directional tests."""
    mineable = frozenset((x, y) for x in range(5, 9) for y in range(5, 9))
    rim = frozenset({(5, 5)})
    inner = mineable - rim
    external_void = _external_void_ring(mineable)
    from tests.support.catalog_test_fixtures import build_minimal_test_catalog_slice

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


def test_candidate_rejects_fixed_output_transport_inside_mineable() -> None:
    inp = _west_rim_greenfield()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(
        inp,
        skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    assert not any(
        fixed_output_transport_cell(c) in inp.mineable_cells for c in result.normal_candidates
    )
    assert any(
        r.rejection_reason is CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE
        for r in result.rejected_candidates
    )


def test_candidate_allow_policy_may_admit_more_normals_than_strict() -> None:
    inp = _west_rim_greenfield()
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    strict = generate_candidates(
        inp,
        skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    loose = generate_candidates(
        inp,
        skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.ALLOW,
    )
    assert len(loose.normal_candidates) >= len(strict.normal_candidates)


def test_incremental_commit_never_confirms_candidate_with_mineable_fot(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.ALLOW,
    )
    bad = next(
        c
        for c in generation.normal_candidates
        if fixed_output_transport_cell(c) in inp.mineable_cells
    )
    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=(bad.candidate_id,)),
        {bad.candidate_id: bad},
        inp,
        skeleton,
        domain=domain,
    )
    assert bad.candidate_id not in result.committed_ids
    assert any(
        c.reason is CommitConflictReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE
        for c in result.conflicts
    )


def test_validation_fails_confirmed_candidate_with_mineable_fot(
    narrow_corridor_optimization_input: OptimizationInput,
) -> None:
    from tests.support.rttp_narrow_corridor_fixture import (
        NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
        candidate_by_id,
    )

    inp = narrow_corridor_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    generation = generate_candidates(
        inp,
        skeleton,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    cand = candidate_by_id(generation, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    by_id = {cand.candidate_id: cand}
    assert validate_final_layout((cand.candidate_id,), frozenset(), by_id, inp)

    mineable_fot = next(iter(inp.mineable_cells - cand.occupied_cells))
    bad = replace(
        cand,
        pattern=replace(
            cand.pattern,
            fixed_output_transport_offset=(
                mineable_fot[0] - cand.anchor_coord[0],
                mineable_fot[1] - cand.anchor_coord[1],
            ),
        ),
    )
    by_id_bad = {bad.candidate_id: bad}
    assert not validate_final_layout((bad.candidate_id,), frozenset(), by_id_bad, inp)
