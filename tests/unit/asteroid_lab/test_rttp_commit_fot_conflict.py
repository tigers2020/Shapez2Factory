"""Cross-commit: extractor must not occupy a prior commit's fixed_output_transport cell.

Greenfield (mineable x,y in 5..8): FOT sits on ``external_void`` (outside mineable per PR-1).
Peer extractor anchor equals the reserved FOT void cell — cross-commit conflict, not
mineable FOT.
"""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.contracts.catalog_placement import CatalogPlacementRef
from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflictReason,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput, TransportKind
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import (
    RttpSkeletonBuilder,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)
from tests.unit.asteroid_lab.conftest import (
    _external_margin_goals,
    _external_void_ring,
    _perimeter_cells,
)


@pytest.fixture
def fot_conflict_optimization_input(
    catalog_slice_minimal: BuildingCatalogSlice,
) -> OptimizationInput:
    """Isolated 4×4 mineable block — (9,6) stays external void (not narrow-corridor rim)."""

    mineable = frozenset((x, y) for x in range(5, 9) for y in range(5, 9))
    rim = _perimeter_cells(mineable)
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
        route_goals=_external_margin_goals(rim, external_void),
        existing_transport_cells=frozenset(),
        catalog_slice=catalog_slice_minimal,
    )


def _pattern(
    *,
    pattern_id: str,
    output_dir: str,
    fot: Coord,
    stub: Coord,
) -> BundlePattern:
    return BundlePattern(
        pattern_id=pattern_id,
        extension_count=0,
        occupied_offsets=frozenset({(0, 0)}),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_dir=output_dir,
        fixed_output_transport_offset=fot,
        output_stub_offset=stub,
        throughput_factor=4,
        topology_kind="test",
    )


def _candidate(
    candidate_id: str,
    anchor: Coord,
    pattern: BundlePattern,
) -> BundleCandidate:
    occupied = frozenset({anchor})
    stub = (
        anchor[0] + pattern.output_stub_offset[0],
        anchor[1] + pattern.output_stub_offset[1],
    )
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=4,
        route_probe_cost=1,
        reachable=True,
        catalog_placement_ref=CatalogPlacementRef("test", anchor, pattern.output_dir),
    )


def _assert_fot_outside_mineable(
    candidate: BundleCandidate,
    inp: OptimizationInput,
) -> None:
    fot = fixed_output_transport_cell(candidate)
    assert fot not in inp.mineable_cells
    assert fot in inp.external_void_cells


@pytest.mark.parametrize(
    (
        "first_dir",
        "first_anchor",
        "first_fot",
        "first_stub",
        "second_dir",
        "second_anchor",
        "second_fot",
        "second_stub",
    ),
    [
        # W rim (5,6) → FOT (4,6) void; peer tries extractor on reserved void.
        ("W", (5, 6), (-1, 0), (0, 1), "E", (4, 6), (-1, 0), (0, 2)),
        # E rim (8,6) → FOT (9,6) void.
        ("E", (8, 6), (1, 0), (0, 1), "E", (9, 6), (1, 0), (0, 2)),
        ("E", (8, 6), (1, 0), (0, 1), "E", (9, 6), (1, 0), (0, 2)),
    ],
    ids=["w_then_void_peer_n", "e_then_void_peer_w", "e_then_void_peer_n"],
)
def test_first_miner_fot_blocked_by_later_extractor_on_fot_cell(
    fot_conflict_optimization_input: OptimizationInput,
    first_dir: str,
    first_anchor: Coord,
    first_fot: Coord,
    first_stub: Coord,
    second_dir: str,
    second_anchor: Coord,
    second_fot: Coord,
    second_stub: Coord,
) -> None:
    """Cross-commit FOT reservation for N/E/S output axes (greenfield mineable grid)."""
    first_pattern = _pattern(
        pattern_id=first_dir.lower(),
        output_dir=first_dir,
        fot=first_fot,
        stub=first_stub,
    )
    second_pattern = _pattern(
        pattern_id=second_dir.lower(),
        output_dir=second_dir,
        fot=second_fot,
        stub=second_stub,
    )
    first_cand = _candidate(f"first:{first_anchor}", first_anchor, first_pattern)
    second_cand = _candidate(f"second:{second_anchor}", second_anchor, second_pattern)
    inp = fot_conflict_optimization_input
    assert fixed_output_transport_cell(first_cand) == second_anchor
    _assert_fot_outside_mineable(first_cand, inp)
    assert second_anchor not in inp.mineable_cells
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    by_id = {first_cand.candidate_id: first_cand, second_cand.candidate_id: second_cand}
    result = incremental_commit(
        PlacementGenome(commit_order=(first_cand.candidate_id, second_cand.candidate_id)),
        by_id,
        inp,
        skeleton,
        domain=initial_commit_domain(skeleton, inp),
    )
    assert first_cand.candidate_id in result.committed_ids
    assert second_cand.candidate_id not in result.committed_ids
    assert any(
        c.candidate_id == second_cand.candidate_id
        and c.reason is CommitConflictReason.FIXED_OUTPUT_TRANSPORT_CONFLICT
        for c in result.conflicts
    )


def test_n_miner_fot_blocked_by_later_w_extractor_at_same_cell(
    fot_conflict_optimization_input: OptimizationInput,
) -> None:
    """Regression: W@(5,6) FOT (4,6) void; peer N@(4,6) must not commit (Lab void peer)."""

    w_pattern = _pattern(pattern_id="w", output_dir="W", fot=(-1, 0), stub=(0, 1))
    n_pattern = _pattern(pattern_id="peer", output_dir="E", fot=(-1, 0), stub=(0, 2))
    w_anchor: Coord = (5, 6)
    peer_void: Coord = (4, 6)
    w_cand = _candidate("w:5,6", w_anchor, w_pattern)
    n_cand = _candidate("n:4,6", peer_void, n_pattern)
    inp = fot_conflict_optimization_input
    assert fixed_output_transport_cell(w_cand) == peer_void
    _assert_fot_outside_mineable(w_cand, inp)
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = initial_commit_domain(skeleton, inp)
    by_id = {n_cand.candidate_id: n_cand, w_cand.candidate_id: w_cand}
    result = incremental_commit(
        PlacementGenome(commit_order=(w_cand.candidate_id, n_cand.candidate_id)),
        by_id,
        inp,
        skeleton,
        domain=domain,
    )
    assert w_cand.candidate_id in result.committed_ids
    assert n_cand.candidate_id not in result.committed_ids
    assert any(
        c.candidate_id == n_cand.candidate_id
        and c.reason is CommitConflictReason.FIXED_OUTPUT_TRANSPORT_CONFLICT
        for c in result.conflicts
    )
    assert validate_final_layout(result.committed_ids, result.reserved_route_cells, by_id, inp)


def test_w_miner_first_blocks_n_fot_on_same_cell(
    fot_conflict_optimization_input: OptimizationInput,
) -> None:
    w_pattern = _pattern(pattern_id="w", output_dir="W", fot=(-1, 0), stub=(0, 1))
    n_pattern = _pattern(pattern_id="peer", output_dir="E", fot=(-1, 0), stub=(0, 2))
    peer_void: Coord = (4, 6)
    w_cand = _candidate("w:5,6", (5, 6), w_pattern)
    n_cand = _candidate("n:4,6", peer_void, n_pattern)
    inp = fot_conflict_optimization_input
    _assert_fot_outside_mineable(w_cand, inp)
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = incremental_commit(
        PlacementGenome(commit_order=(w_cand.candidate_id, n_cand.candidate_id)),
        {n_cand.candidate_id: n_cand, w_cand.candidate_id: w_cand},
        inp,
        skeleton,
        domain=initial_commit_domain(skeleton, inp),
    )
    assert w_cand.candidate_id in result.committed_ids
    assert n_cand.candidate_id not in result.committed_ids
    assert any(
        c.candidate_id == n_cand.candidate_id
        and c.reason is CommitConflictReason.FIXED_OUTPUT_TRANSPORT_CONFLICT
        for c in result.conflicts
    )


def test_validate_final_layout_rejects_extractor_on_peer_fot(
    fot_conflict_optimization_input: OptimizationInput,
) -> None:
    w_pattern = _pattern(pattern_id="w", output_dir="W", fot=(-1, 0), stub=(0, 1))
    n_pattern = _pattern(pattern_id="peer", output_dir="E", fot=(-1, 0), stub=(0, 2))
    peer_void: Coord = (4, 6)
    w_cand = _candidate("w", (5, 6), w_pattern)
    n_cand = _candidate("n", peer_void, n_pattern)
    by_id = {n_cand.candidate_id: n_cand, w_cand.candidate_id: w_cand}
    assert (
        validate_final_layout(
            (w_cand.candidate_id, n_cand.candidate_id),
            frozenset(),
            by_id,
            fot_conflict_optimization_input,
        )
        is False
    )
