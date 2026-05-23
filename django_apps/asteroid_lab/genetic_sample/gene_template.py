"""Gene topology templates for genetic sample admin (canonical E; not solver runtime)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

CANONICAL_EXTRACTOR_OFFSET: Coord = (0, 0)
CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET: Coord = (1, 0)
CANONICAL_ROUTE_PROBE_START_OFFSET: Coord = (2, 0)
CANONICAL_OUTPUT_DIR: Direction = Direction.E

VALID_THROUGHPUT_FACTORS: frozenset[int] = frozenset({4, 8, 12, 16})


@dataclass(frozen=True, slots=True)
class ExtensionAttachment:
    parent_offset: Coord
    child_offset: Coord
    attach_dir: str


@dataclass(frozen=True, slots=True)
class GeneTemplate:
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
    extension_attachments: tuple[ExtensionAttachment, ...] = ()

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


def extension_attachments_parent_first(
    attachments: tuple[ExtensionAttachment, ...],
) -> tuple[ExtensionAttachment, ...]:
    if len(attachments) <= 1:
        return attachments

    child_offsets = {edge.child_offset for edge in attachments}
    edges_by_child = {edge.child_offset: edge for edge in attachments}
    in_degree: dict[Coord, int] = dict.fromkeys(child_offsets, 0)
    children_by_parent: dict[Coord, list[Coord]] = {}

    for edge in attachments:
        if edge.parent_offset == CANONICAL_EXTRACTOR_OFFSET:
            continue
        if edge.parent_offset not in child_offsets:
            continue
        in_degree[edge.child_offset] += 1
        children_by_parent.setdefault(edge.parent_offset, []).append(edge.child_offset)

    ready = sorted(
        (off for off, deg in in_degree.items() if deg == 0),
        key=lambda c: (c[0], c[1]),
    )
    ordered_child_offs: list[Coord] = []
    while ready:
        parent_off = ready.pop(0)
        ordered_child_offs.append(parent_off)
        for child_off in sorted(
            children_by_parent.get(parent_off, ()),
            key=lambda c: (c[0], c[1]),
        ):
            in_degree[child_off] -= 1
            if in_degree[child_off] == 0:
                ready.append(child_off)
        ready.sort(key=lambda c: (c[0], c[1]))

    if len(ordered_child_offs) != len(attachments):
        return attachments

    return tuple(edges_by_child[child_off] for child_off in ordered_child_offs)


def throughput_factor_for_extension_count(extension_count: int) -> int:
    if extension_count < 0 or extension_count > 3:
        msg = "extension_count must be 0..3"
        raise ValueError(msg)
    return 4 * (1 + extension_count)


__all__ = [
    "CANONICAL_EXTRACTOR_OFFSET",
    "CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET",
    "CANONICAL_OUTPUT_DIR",
    "CANONICAL_ROUTE_PROBE_START_OFFSET",
    "ExtensionAttachment",
    "GeneTemplate",
    "extension_attachments_parent_first",
    "throughput_factor_for_extension_count",
]
