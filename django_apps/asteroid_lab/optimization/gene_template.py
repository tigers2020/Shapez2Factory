"""Gene topology templates for candidate projection (canonical E, Server relative offsets)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import Direction

# Canonical E layout (relative Server Coord, extractor at origin).
CANONICAL_EXTRACTOR_OFFSET: Coord = (0, 0)
CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET: Coord = (1, 0)
CANONICAL_ROUTE_PROBE_START_OFFSET: Coord = (2, 0)
CANONICAL_OUTPUT_DIR: Direction = Direction.E

VALID_THROUGHPUT_FACTORS: frozenset[int] = frozenset({4, 8, 12, 16})


@dataclass(frozen=True, slots=True)
class GeneTemplate:
    """Relative extractor-extension topology; canonical ``output_dir`` is E.

    ``occupied_offsets`` holds extractor + extensions only (no belt/pipe cell).
    ``fixed_output_transport_offset`` is the mandatory R-side transport stub (not occupied).
    ``route_probe_start_offset`` is where Phase 4 route probe will start (not occupied).
    """

    gene_id: str
    name: str
    occupied_offsets: frozenset[Coord]
    extractor_offset: Coord
    extension_offsets: tuple[Coord, ...]
    output_dir: Direction
    fixed_output_transport_offset: Coord
    route_probe_start_offset: Coord
    throughput_factor: int
    topology_signature_base: str

    def __post_init__(self) -> None:
        if self.output_dir is not Direction.E:
            msg = "GeneTemplate must be stored in canonical E (output_dir=E)"
            raise ValueError(msg)
        if self.extractor_offset != CANONICAL_EXTRACTOR_OFFSET:
            msg = "canonical extractor_offset must be (0, 0)"
            raise ValueError(msg)
        if self.throughput_factor not in VALID_THROUGHPUT_FACTORS:
            msg = f"throughput_factor must be one of {sorted(VALID_THROUGHPUT_FACTORS)}"
            raise ValueError(msg)
        if self.fixed_output_transport_offset in self.occupied_offsets:
            msg = "fixed_output_transport_offset must not be in occupied_offsets"
            raise ValueError(msg)
        if self.route_probe_start_offset in self.occupied_offsets:
            msg = "route_probe_start_offset must not be in occupied_offsets"
            raise ValueError(msg)
        if len(self.occupied_offsets) != len({self.extractor_offset, *self.extension_offsets}):
            msg = "occupied_offsets must equal extractor + extensions without overlap"
            raise ValueError(msg)


def throughput_factor_for_extension_count(extension_count: int) -> int:
    """Game rule: base x4 + x4 per extension (max 3 extensions -> x16)."""

    if extension_count < 0 or extension_count > 3:
        msg = "extension_count must be 0..3"
        raise ValueError(msg)
    return 4 * (1 + extension_count)
