"""Track D+ PR-3 — catalog-native candidate generator tests."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.adapters.catalog_candidate_placements import (
    build_catalog_placement_specs,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    CandidateRejectReason,
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


def test_generate_candidates_all_normal_have_catalog_ref(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.ALLOW,
    )
    assert result.normal_candidates
    for cand in result.normal_candidates:
        assert cand.catalog_placement_ref is not None
        assert cand.pattern.pattern_id.startswith("cat_")
        assert "lin_" not in cand.pattern.pattern_id


def test_generate_candidates_slice_none_returns_empty_normal(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = replace(greenfield_optimization_input, catalog_slice=None)
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(inp, skeleton)
    assert result.normal_candidates == ()
    assert result.rejected_candidates == ()


def test_normal_occupied_matches_catalog_placement_spec(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.ALLOW,
    )
    sl = inp.catalog_slice
    assert sl is not None
    specs = build_catalog_placement_specs(sl, transport_kind=inp.transport_kind)
    for cand in result.normal_candidates:
        ref = cand.catalog_placement_ref
        assert ref is not None
        spec = next(
            s
            for s in specs
            if s.canonical_id == ref.canonical_id and s.rotation == ref.rotation
        )
        expected = frozenset(
            (ref.anchor_coord[0] + off[0], ref.anchor_coord[1] + off[1])
            for off in spec.occupied_offsets
        )
        assert cand.occupied_cells == expected
        assert cand.pattern.extension_offsets == ()
        fot = (
            ref.anchor_coord[0] + cand.pattern.fixed_output_transport_offset[0],
            ref.anchor_coord[1] + cand.pattern.fixed_output_transport_offset[1],
        )
        assert fot not in cand.occupied_cells


def test_normal_candidate_has_empty_extensions_and_fot_not_occupied(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    for cand in result.normal_candidates:
        fot = (
            cand.anchor_coord[0] + cand.pattern.fixed_output_transport_offset[0],
            cand.anchor_coord[1] + cand.pattern.fixed_output_transport_offset[1],
        )
        assert fot not in inp.mineable_cells
    assert any(
        r.rejection_reason is CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_INSIDE_MINEABLE
        for r in result.rejected_candidates
    )
    result_allow = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.ALLOW,
    )
    assert result_allow.normal_candidates
    cand = result_allow.normal_candidates[0]
    anchor = cand.anchor_coord
    fot = (
        anchor[0] + cand.pattern.fixed_output_transport_offset[0],
        anchor[1] + cand.pattern.fixed_output_transport_offset[1],
    )
    assert cand.pattern.extension_offsets == ()
    assert fot not in cand.occupied_cells
    assert cand.throughput_factor == 4
