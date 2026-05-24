"""Track D+ PR-3 — catalog-native candidate generator tests."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    expected_footprint_coords,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
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
    result = generate_candidates(inp, skeleton, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)
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


def test_normal_occupied_matches_catalog_footprint(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(inp, skeleton, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)
    sl = inp.catalog_slice
    assert sl is not None
    for cand in result.normal_candidates:
        ref = cand.catalog_placement_ref
        assert ref is not None
        geom = next(
            g for g in sl.variant_geometries if g.canonical_id == ref.canonical_id
        )
        expected = expected_footprint_coords(
            geom.footprint_cells,
            anchor_coord=ref.anchor_coord,
            rotation=ref.rotation,
        )
        assert cand.occupied_cells == expected
