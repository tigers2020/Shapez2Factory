"""Selection must not schedule miners whose occupied/FOT cells cross (PR1.5)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput, TransportKind
from django_apps.asteroid_lab.optimization.selection.greedy_regret import select_genome
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import (
    RttpSkeletonBuilder,
    RttpSkeletonConfig,
)


def _candidate(
    candidate_id: str,
    anchor: tuple[int, int],
    *,
    output_dir: str,
    fot: tuple[int, int],
    stub: tuple[int, int],
) -> BundleCandidate:
    pattern = BundlePattern(
        pattern_id=output_dir.lower(),
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
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=frozenset({anchor}),
        output_stub=(anchor[0] + stub[0], anchor[1] + stub[1]),
        output_dir=output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=4,
        route_probe_cost=1,
        reachable=True,
    )


def test_select_genome_excludes_fot_conflicting_second_miner(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    """N@(6,7) FOT (6,6); W@(6,6) must not appear in genome when goal_count=2."""
    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    n = _candidate("n:6,7", (6, 7), output_dir="N", fot=(0, -1), stub=(0, -2))
    w = _candidate("w:6,6", (6, 6), output_dir="W", fot=(-1, 0), stub=(-2, 0))
    assert fixed_output_transport_cell(n) == (6, 6)
    genome = select_genome((n, w), skeleton, inp, goal_count=2)
    assert genome.commit_order == (n.candidate_id,)
