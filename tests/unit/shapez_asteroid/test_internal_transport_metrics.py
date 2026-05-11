"""Canonical internal transport counts (is_external) + STEP4 corridor merge for Pass3/P4."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridor_read_factory import (  # noqa: E501
    protected_corridors_read_from_routing_state,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
    merge_step4_corridor_routing_mapping,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.internal_transport_metrics import (  # noqa: E501
    count_internal_transport_cells,
    count_internal_transport_tiles_for_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
    count_internal_transport_tiles_for_kind,
)


def _never_ext(_c: tuple[int, int]) -> bool:
    return False


def _ext_x_gt_5(c: tuple[int, int]) -> bool:
    return c[0] > 5


def test_count_internal_transport_cells_respects_is_external() -> None:
    cells = {(3, 0), (7, 0), (8, 0)}
    assert count_internal_transport_cells(cells, is_external=_never_ext) == 3
    assert count_internal_transport_cells(cells, is_external=_ext_x_gt_5) == 1


def test_count_internal_transport_tiles_for_kind_matches_role_helper() -> None:
    cells = {
        (1, 0): {"role": "belt", "x": 1, "y": 0},
        (10, 0): {"role": "belt", "x": 10, "y": 0},
        (2, 0): {"role": "pipe", "x": 2, "y": 0},
    }
    tk = "shape_belt"
    wr = want_role(tk)
    a = count_internal_transport_tiles_for_kind(cells, transport_kind=tk, is_external=_ext_x_gt_5)
    b = count_internal_transport_tiles_for_role(cells, want_role=wr, is_external=_ext_x_gt_5)
    assert a == b == 1


def test_merge_step4_corridor_routing_mapping_for_pass3_read_factory() -> None:
    rs = {"hard_protected_corridors": [[1, 1], [2, 2]]}
    merged = merge_step4_corridor_routing_mapping(routing_state=rs, trunk_load={})
    assert merged is not None
    dto = protected_corridors_read_from_routing_state(merged)
    assert len(dto.hard) == 2
    assert (1, 1) in dto.hard and (2, 2) in dto.hard
