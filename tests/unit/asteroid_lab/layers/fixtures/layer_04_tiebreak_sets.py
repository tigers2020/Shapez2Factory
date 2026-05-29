"""Component with competing maximal sets for set_score tie-break tests."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbedBundleCandidate
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def tiebreak_count_component_probes() -> tuple[RouteProbedBundleCandidate, ...]:
    """Star graph: blocker gain 4 vs three disjoint verticals (gain 2 each, total 6)."""

    blocker = succeeded_probe_at(
        (2, 0),
        equivalence_key="blocker",
        output_dir=Direction.E,
        mining=frozenset({(0, 0), (1, 0), (2, 0), (3, 0)}),
        transport=frozenset({(4, 0)}),
    )
    verticals: list[RouteProbedBundleCandidate] = []
    for x in (0, 2, 4):
        verticals.append(
            succeeded_probe_at(
                (x, 0),
                equivalence_key=f"vert_{x}",
                output_dir=Direction.S,
                mining=frozenset({(x, 0), (x, 1)}),
                transport=frozenset({(x, 9)}),
            )
        )
    return (blocker, *verticals)


def tiebreak_route_cost_component_probes() -> tuple[RouteProbedBundleCandidate, ...]:
    """Single conflict pair: same gain; lower route_cost wins."""

    cheap = succeeded_probe_at(
        (0, 0),
        equivalence_key="cheap",
        output_dir=Direction.W,
        mining=frozenset({(0, 0)}),
        transport=frozenset({(9, 0)}),
        route_cost=1,
    )
    costly = succeeded_probe_at(
        (0, 0),
        equivalence_key="costly",
        output_dir=Direction.E,
        mining=frozenset({(0, 0)}),
        transport=frozenset({(8, 0)}),
        route_cost=50,
    )
    return (cheap, costly)


__all__ = [
    "tiebreak_count_component_probes",
    "tiebreak_route_cost_component_probes",
]
