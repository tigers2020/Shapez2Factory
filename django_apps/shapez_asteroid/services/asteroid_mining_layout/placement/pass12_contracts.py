"""Pass1/Pass2 placement commit DTO contracts."""

from __future__ import annotations

from dataclasses import dataclass, field

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
)


@dataclass
class Pass12LayoutScratch:
    """Mutable belt/pipe cells and building bodies during Pass1/Pass2."""

    transport_cells: set[Coord] = field(default_factory=set)
    blocked_cells: set[Coord] = field(default_factory=set)
    extractor_cells: set[Coord] = field(default_factory=set)
    extension_facings: dict[Coord, tuple[int, int]] = field(default_factory=dict)
    extractor_output_dirs: dict[Coord, tuple[int, int]] = field(default_factory=dict)
    transport_kind: str = "shape_belt"
    next_placement_seq: int = 0
    placement_records: dict[str, PlacementCommitRecord] = field(default_factory=dict)


@dataclass(frozen=True)
class Pass12ScratchBaseline:
    """Immutable snapshot for rollback on probe/merge exceptions (Pass12 bundle gate)."""

    transport_cells: frozenset[Coord]
    blocked_cells: frozenset[Coord]
    extractor_cells: frozenset[Coord]
    extension_facings: frozenset[tuple[Coord, int, int]]
    extractor_output_dirs: frozenset[tuple[Coord, int, int]]
    transport_kind: str
    next_placement_seq: int
    placement_records: dict[str, PlacementCommitRecord]


@dataclass(frozen=True)
class Pass12BundleCandidate:
    """Hypothetical delta if the route probe succeeds."""

    blocked_cells: frozenset[Coord]
    new_transport: frozenset[Coord]
    stub_cell: Coord
    extractor_cell: Coord | None = None
    extension_facings: frozenset[tuple[Coord, int, int]] = field(default_factory=frozenset)
    extractor_output_dir: tuple[int, int] | None = None
    p1_cheap_void_cells: frozenset[Coord] | None = None
    placement_pass: str = "pass1"
