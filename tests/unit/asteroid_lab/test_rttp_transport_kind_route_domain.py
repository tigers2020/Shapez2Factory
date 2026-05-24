"""B2-T3 — transport-kind aware route domain (Policy B)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.input_contracts import (
    ExistingTransportCell,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    mismatched_existing_transport_metrics,
    optimization_input_from_reconstruction,
    partition_existing_transport,
)
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    build_route_domain_from_skeleton,
)
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
from django_apps.asteroid_lab.optimization.routing.route_probe import probe_route
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import (
    RttpSkeletonBuilder,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from tests.unit.asteroid_lab.test_optimization_input_adapter import (
    _belt_cell,
    _field_cell,
    _pipe_cell,
)


def test_partition_existing_transport_shape_active() -> None:
    belt = ExistingTransportCell(coord=(4, 5), transport_kind=TransportKind.SHAPE_BELT)
    pipe = ExistingTransportCell(coord=(4, 6), transport_kind=TransportKind.FLUID_PIPE)
    existing = frozenset({belt, pipe})

    trunk, blocked, by_kind = partition_existing_transport(
        existing, TransportKind.SHAPE_BELT
    )

    assert trunk == frozenset({(4, 5)})
    assert blocked == frozenset({(4, 6)})
    assert by_kind == {"fluid_pipe": 1}
    assert len(blocked) == 1


def _mixed_reconstruction() -> ReconstructionResult:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    return ReconstructionResult(cells=cells + (_belt_cell(4, 5), _pipe_cell(4, 6)))


def test_shape_route_does_not_use_fluid_pipe_trunk_seed() -> None:
    inp = optimization_input_from_reconstruction(_mixed_reconstruction())
    assert inp.transport_kind is TransportKind.SHAPE_BELT
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = build_route_domain_from_skeleton(skeleton, inp)

    assert (4, 6) not in inp.existing_trunk_cells
    assert (4, 6) not in skeleton.trunk_mask_cells
    assert (4, 6) in inp.blocked_incompatible_transport_cells
    assert (4, 6) in domain.blocked_cells
    assert (4, 6) not in domain.trunk_mask_cells
    assert (4, 6) not in domain.traversable_cells
    assert (4, 5) in skeleton.trunk_mask_cells


def test_fluid_route_does_not_use_shape_belt_trunk_seed() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    cells = cells + (_pipe_cell(4, 5), _pipe_cell(4, 6), _belt_cell(3, 5))
    inp = optimization_input_from_reconstruction(ReconstructionResult(cells=cells))
    assert inp.transport_kind is TransportKind.FLUID_PIPE
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = build_route_domain_from_skeleton(skeleton, inp)

    assert (3, 5) not in inp.existing_trunk_cells
    assert (3, 5) not in skeleton.trunk_mask_cells
    assert (3, 5) in domain.blocked_cells
    assert (3, 5) not in domain.traversable_cells


def test_incompatible_on_ring_excluded_from_trunk_not_traversable() -> None:
    """INV-B2T3-08: wrong-kind on ring coord must not be trunk or traversable."""
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    # Belt west of block keeps active kind SHAPE_BELT; pipe on rim corner (5,5).
    cells = cells + (_belt_cell(4, 5), _pipe_cell(5, 5))
    inp = optimization_input_from_reconstruction(ReconstructionResult(cells=cells))
    assert inp.transport_kind is TransportKind.SHAPE_BELT
    assert (5, 5) in inp.blocked_incompatible_transport_cells
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = build_route_domain_from_skeleton(skeleton, inp)

    assert (5, 5) not in skeleton.trunk_mask_cells
    assert (5, 5) not in domain.trunk_mask_cells
    assert (5, 5) not in domain.traversable_cells
    assert (5, 5) in domain.blocked_cells


def test_transport_kind_mismatch_diagnostics_from_partition() -> None:
    belt = ExistingTransportCell(coord=(1, 1), transport_kind=TransportKind.SHAPE_BELT)
    pipe_a = ExistingTransportCell(coord=(2, 2), transport_kind=TransportKind.FLUID_PIPE)
    pipe_b = ExistingTransportCell(coord=(3, 3), transport_kind=TransportKind.FLUID_PIPE)
    _trunk, blocked, by_kind = partition_existing_transport(
        frozenset({belt, pipe_a, pipe_b}), TransportKind.SHAPE_BELT
    )
    metrics = mismatched_existing_transport_metrics(blocked, by_kind=by_kind)
    assert metrics["mismatched_existing_transport_count"] == 2
    assert metrics["mismatched_existing_transport_by_kind"] == {"fluid_pipe": 2}


def test_route_probe_ignores_mismatched_existing_transport_kind() -> None:
    inp = optimization_input_from_reconstruction(_mixed_reconstruction())
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = build_route_domain_from_skeleton(skeleton, inp)
    goals = probe_goal_coords(inp, skeleton)
    assert skeleton.lift_columns
    start = skeleton.lift_columns[0].platform_coord
    result = probe_route(domain, start, goals)
    if result.reachable and result.path:
        assert not (set(result.path) & inp.blocked_incompatible_transport_cells)
