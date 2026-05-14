"""Lexicographic route search DTO contracts."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord

LexTuple = tuple[int, int, int, int, int, int, int, int]


@dataclass(frozen=True)
class RouteSearchResult:
    """lexicographic Dijkstra 결과 DTO."""

    found: bool
    path: tuple[Coord, ...]
    priority: LexTuple | None
    expanded_nodes: int
    search_mode: str
    fallback_reason: str | None
    optimality_guarantee: bool
    search_time_ms: float | None = None
