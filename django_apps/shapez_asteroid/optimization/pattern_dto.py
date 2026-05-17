"""Phase 2 — local bundle pattern DTOs (pattern compiler output only)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.enums import CardinalDirection

# Phase 2 document name ``Direction``; wire values match ``CardinalDirection``.
Direction = CardinalDirection


@dataclass(frozen=True, slots=True)
class ExtensionAttachment:
    extension_offset: Coord
    parent_offset: Coord
    required_facing: Direction


@dataclass(frozen=True, slots=True)
class BundlePattern:
    pattern_id: str
    extension_count: int
    occupied_offsets: frozenset[Coord]
    extractor_offset: Coord
    extension_offsets: tuple[Coord, ...]
    attachments: tuple[ExtensionAttachment, ...]
    output_dir: Direction
    output_stub_offset: Coord
    throughput_factor: int
    topology_kind: str = "linear"
