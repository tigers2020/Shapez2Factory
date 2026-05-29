"""21-node single-component clique via shared transport stub."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbedBundleCandidate
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.exact_pack import (
    MAX_EXACT_COMPONENT_SIZE,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)

_SHARED_STUB = frozenset({(0, 0)})


def large_component_probes() -> tuple[RouteProbedBundleCandidate, ...]:
    count = MAX_EXACT_COMPONENT_SIZE + 1
    probes: list[RouteProbedBundleCandidate] = []
    for i in range(count):
        probes.append(
            succeeded_probe_at(
                (i + 1, 1),
                equivalence_key=f"node_{i}",
                mining=frozenset({(i + 10, 1)}),
                transport=_SHARED_STUB,
            )
        )
    return tuple(probes)


__all__ = ["large_component_probes"]
