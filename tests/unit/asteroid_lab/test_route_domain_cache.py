"""Route domain seed snapshot cache tests."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.route_domain import (
    _SEED_DOMAIN_CACHE,
    RouteDomainSnapshotBuilder,
    clear_seed_domain_cache,
)


def _open_void_input():
    bb = BBox(0, 4, 0, 4)
    void = frozenset(
        (sx, sy) for sx in range(bb.min_sx, bb.max_sx + 1) for sy in range(bb.min_sy, bb.max_sy + 1)
    )
    return replace(greenfield_optimization_input(bbox=bb), external_void_cells=void)


def test_seed_domain_cache_reuses_seed_and_overlay_is_independent() -> None:
    clear_seed_domain_cache()
    inp = _open_void_input()

    d1 = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    d2 = RouteDomainSnapshotBuilder.build_seed_snapshot(inp)
    assert d1 is not d2
    assert len(_SEED_DOMAIN_CACHE) == 1

    d3 = RouteDomainSnapshotBuilder.build_snapshot(
        inp,
        provisional_blocked_cells=frozenset({(1, 0)}),
    )
    assert d3 is not d1
    assert d3[(1, 0)].hard_blocked is True
    assert d1[(1, 0)].hard_blocked is False
