"""Pure DTOs for P4 reclaim shadow scan (no algorithm logic)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


@dataclass(frozen=True)
class _P4BundleEval:
    """P4 Reclaim bundle 후보 평가 DTO.

        gain_ratio, budget, route validation 결과를 함께 담는다 (§12.2).

    상세: documents/Algorithm/mining_solver_cursor_sessions/10_step6_reclaim_loop.md"""

    gain: float
    additional_route_cost: float
    gain_ratio: float
    incremental_internal_transport_added: int
    rejected_reason: str | None
    accepted_shadow: bool
    anchor: Coord
    extension: Coord
    rotation: int
    shadow_route_path: tuple[Coord, ...] | None = None
    # Spatial diversity (search pressure; gain_ratio threshold uses raw gain_ratio only).
    p4_cluster_penalty: float = 0.0
    p4_route_zone_overlap_cells: int = 0
    p4_route_zone_penalty: float = 0.0
    p4_local_cluster_density: float = 0.0
    p4_min_anchor_distance_to_prior: int | None = None
    p4_total_diversity_penalty: float = 0.0
    gain_ratio_adjusted: float | None = None


@dataclass(frozen=True)
class ReclaimShadowScanResult:
    """P4-A scan trace plus raw bundle evals for P4-B1 provisional commit."""

    trace: dict[str, Any]
    evals: list[_P4BundleEval]
    transport_kind: str | None
