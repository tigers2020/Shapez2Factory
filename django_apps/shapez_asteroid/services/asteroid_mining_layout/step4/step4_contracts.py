"""STEP4 routing result contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


@dataclass(frozen=True)
class Step4Route:
    """STEP4가 확정한 한 extractor placement의 stub-to-trunk/external route 기록.

        placement_id로 Pass12 bundle FSM과 매칭된다 (P2-B, §9.6).

    상세: documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md"""

    extractor_cell: Coord
    stub_cell: Coord
    transport_kind: str
    path: tuple[Coord, ...]
    merged_to_existing: bool
    reached_external: bool
    placement_id: str | None = None


@dataclass(frozen=True)
class Step4RoutingResult:
    """STEP4 routing outcome; ``routing_state`` holds corridor policy for reclaim (not trunk)."""

    committed: bool
    map_after_routing: list[dict[str, Any]]
    routes: tuple[Step4Route, ...]
    routing_failures: tuple[dict[str, Any], ...]
    trunk_load: dict[str, Any]
    routing_state: dict[str, Any] | None
    placement_commit_by_id: dict[str, str]
    rolled_back_placement_ids: tuple[str, ...]
    quarantined_placement_ids: tuple[str, ...]
