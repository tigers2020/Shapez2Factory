from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.routing.corridor_probe import (
    MIN_PASS2_GATEWAYS,
    find_reachable_internal_cells,
    probe_pass2_corridor_availability,
)


def _grid(x0: int, x1: int, y0: int, y1: int) -> frozenset[tuple[int, int]]:
    return frozenset((x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1))


def test_probe_fails_when_pass1_seals_all_mineable() -> None:
    """No interior anchor: every mineable cell blocked → no exterior gateway."""

    mineable = _grid(1, 5, 1, 5)
    barrier = mineable
    belts = mineable
    recon = ReconstructionDTO(
        mineable_placement_cells=tuple(sorted(mineable)),
        full_barrier_cells=tuple(sorted(barrier)),
        belt_cells=tuple(sorted(belts)),
        pipe_cells=(),
        asteroid_bbox=BBox(min_x=1, min_y=1, max_x=5, max_y=5),
        external_margin=2,
    )
    ctx = SolverRunContext(run_id="probe_sealed", reconstruction=recon)
    probe = probe_pass2_corridor_availability(
        mineable_cells=mineable,
        pass1_fixed_cells=mineable,
        hard_barrier_cells=frozenset(recon.full_barrier_cells),
        transport_kind=TransportKind.SHAPE_BELT,
        reconstruction=recon,
        ctx=ctx,
    )
    assert probe.connected is False
    assert probe.gateway_count < MIN_PASS2_GATEWAYS


def test_probe_reaches_out_when_center_open() -> None:
    mineable = _grid(1, 5, 1, 5)
    barrier = mineable
    belts = mineable
    recon = ReconstructionDTO(
        mineable_placement_cells=tuple(sorted(mineable)),
        full_barrier_cells=tuple(sorted(barrier)),
        belt_cells=tuple(sorted(belts)),
        pipe_cells=(),
        asteroid_bbox=BBox(min_x=1, min_y=1, max_x=5, max_y=5),
        external_margin=2,
    )
    ctx = SolverRunContext(run_id="probe_ok", reconstruction=recon)
    perimeter = frozenset(c for c in mineable if min(c[0] - 1, 5 - c[0], c[1] - 1, 5 - c[1]) == 0)
    fixed = perimeter - {(3, 1)}
    probe = probe_pass2_corridor_availability(
        mineable_cells=mineable,
        pass1_fixed_cells=fixed,
        hard_barrier_cells=frozenset(recon.full_barrier_cells),
        transport_kind=TransportKind.SHAPE_BELT,
        reconstruction=recon,
        ctx=ctx,
    )
    assert probe.connected is True
    assert probe.gateway_count >= 1


def test_find_reachable_internal_cells_from_anchors() -> None:
    mineable = _grid(1, 4, 1, 4)
    barrier = mineable
    belts = mineable
    recon = ReconstructionDTO(
        mineable_placement_cells=tuple(sorted(mineable)),
        full_barrier_cells=tuple(sorted(barrier)),
        belt_cells=tuple(sorted(belts)),
        pipe_cells=(),
        asteroid_bbox=BBox(min_x=1, min_y=1, max_x=4, max_y=4),
        external_margin=1,
    )
    ctx = SolverRunContext(run_id="reach", reconstruction=recon)
    fixed = frozenset({(2, 1), (2, 2), (2, 3)})
    r = find_reachable_internal_cells(
        mineable_cells=mineable,
        pass1_fixed_cells=fixed,
        transport_kind=TransportKind.SHAPE_BELT,
        reconstruction=recon,
        ctx=ctx,
    )
    assert len(r) >= 1
