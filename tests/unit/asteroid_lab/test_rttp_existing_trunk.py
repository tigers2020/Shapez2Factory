"""RTTP P1 map class ??existing trunk from reconstruction (PR-6)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO


def _field_cell(sx: int, sy: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=sx,
        y=sy,
        layer=None,
        rotation=0,
        tile_type="AsteroidShapeField",
        cell_kind="asteroid_shape_field",
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"X": sx, "Y": sy, "T": "AsteroidShapeField"},
    )


def _belt_cell(sx: int, sy: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=sx,
        y=sy,
        layer=None,
        rotation=0,
        tile_type="SpaceBelt_Forward",
        cell_kind="space_belt",
        transport_kind="shape_belt",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"X": sx, "Y": sy, "T": "SpaceBelt_Forward"},
    )


def _existing_trunk_reconstruction_result() -> ReconstructionResult:
    """4횞4 mineable block with one west-rim belt cell as existing trunk."""

    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    cells = cells + (_belt_cell(4, 5),)
    return ReconstructionResult(cells=cells)


def _existing_trunk_optimization_input() -> OptimizationInput:
    return optimization_input_from_reconstruction(_existing_trunk_reconstruction_result())


def test_skeleton_includes_existing_trunk_cells() -> None:
    inp = _existing_trunk_optimization_input()

    assert inp.existing_trunk_cells
    assert inp.existing_trunk_cells <= frozenset(
        cell.coord for cell in inp.existing_transport_cells
    )

    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())

    assert inp.existing_trunk_cells <= skeleton.trunk_mask_cells
    assert inp.existing_trunk_cells.issubset(skeleton.trunk_mask_cells)


def test_reachable_candidate_attaches_to_existing_trunk() -> None:
    inp = _existing_trunk_optimization_input()

    assert inp.existing_trunk_cells
    assert inp.route_goals
    assert inp.transport_kind is TransportKind.SHAPE_BELT

    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(inp, skeleton, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)

    assert len(result.normal_candidates) >= 1
    assert any(candidate.reachable for candidate in result.normal_candidates)


def test_existing_trunk_pipeline_commits_deterministically() -> None:
    """P1 map class: full pipeline (select → commit) on reconstruction-seeded trunk."""

    inp = _existing_trunk_optimization_input()
    first = run_rttp_pipeline(inp, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)
    second = run_rttp_pipeline(inp, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)

    assert first.normal_count >= 1
    assert len(first.commit_result.committed_ids) >= 1
    assert first.validation_passed
    assert first == second
    assert first.commit_result.committed_ids == second.commit_result.committed_ids
    assert first.genome.commit_order == second.genome.commit_order
