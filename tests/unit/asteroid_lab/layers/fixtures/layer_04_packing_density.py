"""Star-graph packing-density fixture (blocker vs five disjoint verticals)."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbedBundleCandidate
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def packing_density_probes() -> tuple[RouteProbedBundleCandidate, ...]:
    blocker_a = succeeded_probe_at(
        (2, 2),
        equivalence_key="blocker_a",
        output_dir=Direction.E,
        mining=frozenset({(0, 2), (1, 2), (3, 2), (4, 2)}),
        transport=frozenset({(5, 2)}),
    )
    verticals: list[RouteProbedBundleCandidate] = []
    for x in (0, 1, 3, 4, 5):
        verticals.append(
            succeeded_probe_at(
                (x, 0),
                equivalence_key=f"vert_{x}",
                output_dir=Direction.S,
                mining=frozenset({(x, y) for y in range(4)}),
                transport=frozenset({(x, 9)}),
            )
        )
    return (blocker_a, *verticals)


__all__ = ["packing_density_probes"]
