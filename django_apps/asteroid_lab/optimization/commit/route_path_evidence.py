"""Commit-time route path evidence (output-only; not solver input)."""

from __future__ import annotations

import hashlib
from typing import Any

from django_apps.asteroid_lab.optimization.routing.route_probe import RouteProbeResult


def build_route_path_evidence(
    *,
    candidate_id: str,
    probe: RouteProbeResult,
) -> dict[str, Any]:
    path = probe.path
    reached = probe.reached_goal
    return {
        "candidate_id": candidate_id,
        "reached_goal": list(reached) if reached is not None else None,
        "path_cost": probe.cost,
        "path_length": len(path),
        "path_hash": hashlib.sha256(repr(path).encode()).hexdigest()[:16],
    }


__all__ = ["build_route_path_evidence"]
