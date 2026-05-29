"""Corner outer-rim W/S overlap probes for L4 mining-first selection (test-only)."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbedBundleCandidate
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)

_CORNER_ANCHOR = (7, 3)
_W_MINING = frozenset({(7, 3), (6, 3), (5, 3), (7, 2), (6, 2), (5, 2)})
_S_MINING = frozenset(
    {
        (7, 3),
        (7, 4),
        (7, 5),
        (6, 3),
        (6, 4),
        (6, 5),
        (5, 3),
        (5, 4),
        (5, 5),
    }
)
_SHARED_STUB = frozenset({(8, 3)})


def corner_ws_w_probe() -> RouteProbedBundleCandidate:
    return succeeded_probe_at(
        _CORNER_ANCHOR,
        equivalence_key="corner_ws_w",
        mining=_W_MINING,
        transport=_SHARED_STUB,
        output_dir=Direction.W,
        route_cost=10,
        goal=(0, 3),
    )


def corner_ws_s_probe() -> RouteProbedBundleCandidate:
    return succeeded_probe_at(
        _CORNER_ANCHOR,
        equivalence_key="corner_ws_s",
        mining=_S_MINING,
        transport=_SHARED_STUB,
        output_dir=Direction.S,
        route_cost=10,
        goal=(7, 8),
    )


__all__ = ["corner_ws_s_probe", "corner_ws_w_probe"]
