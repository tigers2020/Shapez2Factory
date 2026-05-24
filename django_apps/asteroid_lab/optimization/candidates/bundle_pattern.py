"""Bundle pattern DTO shared by catalog-native generator and synthetic lin_* tests."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord


@dataclass(frozen=True, slots=True)
class BundlePattern:
    pattern_id: str
    extension_count: int
    occupied_offsets: frozenset[Coord]
    extractor_offset: Coord
    extension_offsets: tuple[Coord, ...]
    output_dir: str
    output_stub_offset: Coord
    throughput_factor: int
    topology_kind: str


__all__ = ["BundlePattern"]
