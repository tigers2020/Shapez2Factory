"""Deterministic topology_signature strings for bundle candidates (Sequence 3)."""

from __future__ import annotations

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.enums import CardinalDirection, TransportKind
from django_apps.shapez_asteroid.optimization.pattern_dto import BundlePattern


def canonical_rotation_id(output_dir: CardinalDirection) -> int:
    """Stable id matching ``build_pattern_library`` rotation order (N,E,S,W)."""

    order = (
        CardinalDirection.NORTH,
        CardinalDirection.EAST,
        CardinalDirection.SOUTH,
        CardinalDirection.WEST,
    )
    return order.index(output_dir)


def occupied_geometry_summary(occupied_cells: frozenset[Coord]) -> str:
    """Lexicographic occupied geometry (no short unstable abbrev-only signatures)."""

    parts = [f"{c.x},{c.y}" for c in sorted(occupied_cells, key=lambda z: (z.x, z.y))]
    return ";".join(parts)


def build_topology_signature(
    *,
    pattern: BundlePattern,
    transport_kind: TransportKind,
    base_throughput: int,
    absolute_occupied: frozenset[Coord],
    output_stub: Coord,
    output_dir: CardinalDirection,
) -> str:
    """Serialize required components in a single deterministic string."""

    rot = canonical_rotation_id(output_dir)
    geo = occupied_geometry_summary(absolute_occupied)
    return (
        f"pattern_id={pattern.pattern_id}"
        f"|ext_count={pattern.extension_count}"
        f"|canon_rot={rot}"
        f"|out_stub={output_stub.x},{output_stub.y}"
        f"|out_dir={output_dir.value}"
        f"|transport={transport_kind.value}"
        f"|throughput={base_throughput}"
        f"|occupied_geo={geo}"
    )
