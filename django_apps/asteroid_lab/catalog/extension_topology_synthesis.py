"""Production-safe extension topology synthesis (RTTP S2b-1).

S2b-1 emits opposite-arm linear chains only (extension_count 0..3 per rotation).
S2b-2 may add perpendicular N/S arm families in a follow-on spec.

Keep extension arm math in catalog production code only.
Do not import optimization.candidates.pattern_library here:
pattern_library contains test/legacy candidate patterns whose linear E variants
place extensions on the output axis and are forbidden for S2b production synthesis.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import cardinal_unit_vector
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.genetic_sample.gene_template import (
    throughput_factor_for_extension_count,
)
from django_apps.asteroid_lab.optimization.coords import Coord

_OPPOSITE_ARM: dict[CardinalDirection, CardinalDirection] = {
    CardinalDirection.E: CardinalDirection.W,
    CardinalDirection.W: CardinalDirection.E,
    CardinalDirection.N: CardinalDirection.S,
    CardinalDirection.S: CardinalDirection.N,
}


class ExtensionTopologyKind(StrEnum):
    NONE = "none"
    LINEAR_OPPOSITE_ARM = "linear_opposite_arm"


@dataclass(frozen=True, slots=True)
class ExtensionTopology:
    extension_offsets: tuple[Coord, ...]
    extension_count: int
    topology_kind: ExtensionTopologyKind
    synthesis_arm: CardinalDirection


def _linear_offsets_on_arm(arm: CardinalDirection, extension_count: int) -> tuple[Coord, ...]:
    if extension_count < 0 or extension_count > 3:
        msg = "extension_count must be 0..3"
        raise ValueError(msg)
    if extension_count == 0:
        return ()
    unit = cardinal_unit_vector(arm)
    return tuple((unit[0] * (index + 1), unit[1] * (index + 1)) for index in range(extension_count))


def synthesize_opposite_arm_linear_topologies(
    *,
    output_dir: CardinalDirection,
    max_extension_count: int = 3,
) -> tuple[ExtensionTopology, ...]:
    """Return ext 0..max_extension_count on the arm opposite ``output_dir``."""

    if max_extension_count < 0 or max_extension_count > 3:
        msg = "max_extension_count must be 0..3"
        raise ValueError(msg)
    opposite = _OPPOSITE_ARM[output_dir]
    topologies: list[ExtensionTopology] = []
    for extension_count in range(max_extension_count + 1):
        offsets = _linear_offsets_on_arm(opposite, extension_count)
        kind = (
            ExtensionTopologyKind.NONE
            if extension_count == 0
            else ExtensionTopologyKind.LINEAR_OPPOSITE_ARM
        )
        topologies.append(
            ExtensionTopology(
                extension_offsets=offsets,
                extension_count=extension_count,
                topology_kind=kind,
                synthesis_arm=opposite,
            )
        )
    return tuple(topologies)


def throughput_factor_for_topology(topology: ExtensionTopology) -> int:
    return throughput_factor_for_extension_count(topology.extension_count)


__all__ = [
    "ExtensionTopology",
    "ExtensionTopologyKind",
    "synthesize_opposite_arm_linear_topologies",
    "throughput_factor_for_topology",
]
