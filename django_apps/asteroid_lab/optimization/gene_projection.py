"""Project canonical-E gene templates onto absolute Server Coords (no raw conversion).

Phase 4 route probe should use ``ProjectedGenePlacement.route_probe_start`` as
``RouteProbeInput.start``. Overlay bundle occupancy via
``RouteDomainSnapshotBuilder.build_snapshot(..., committed_occupied_cells=...)``
as *provisional* geometry only — CandidateGenerator must not commit placements.
"""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coord_transform import (
    rotate_offset,
    steps_from_canonical_e,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import Direction
from django_apps.asteroid_lab.optimization.gene_template import GeneTemplate


@dataclass(frozen=True, slots=True)
class ProjectedGenePlacement:
    """Absolute Server Coord placement after anchor + rotation."""

    occupied_cells: frozenset[Coord]
    extractor: Coord
    extensions: tuple[Coord, ...]
    fixed_output_transport: Coord
    route_probe_start: Coord
    output_dir: Direction


def _translate(anchor: Coord, rel: Coord, steps: int) -> Coord:
    rx, ry = rotate_offset(rel, steps)
    ax, ay = anchor
    return (ax + rx, ay + ry)


def project_gene_placement(
    *,
    anchor: Coord,
    rotation: Direction,
    gene: GeneTemplate,
) -> ProjectedGenePlacement:
    """Place ``gene`` with extractor at ``anchor`` and bundle output facing ``rotation``."""

    steps = steps_from_canonical_e(rotation)
    occupied_cells = frozenset(_translate(anchor, rel, steps) for rel in gene.occupied_offsets)
    extensions = tuple(
        sorted(
            (_translate(anchor, rel, steps) for rel in gene.extension_offsets),
            key=lambda c: (c[0], c[1]),
        )
    )
    return ProjectedGenePlacement(
        occupied_cells=occupied_cells,
        extractor=_translate(anchor, gene.extractor_offset, steps),
        extensions=extensions,
        fixed_output_transport=_translate(anchor, gene.fixed_output_transport_offset, steps),
        route_probe_start=_translate(anchor, gene.route_probe_start_offset, steps),
        output_dir=rotation,
    )
