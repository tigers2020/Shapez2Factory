"""
Merge-aware capacity-aware routing (STEP 4 §9).

MVP: geometry + kind separation + ``trunk_load`` aggregate trace only (no rated overflow).
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass2Result,
    RoutingResult,
    SolverRunContext,
)


class MergeAwareRouter:
    """Coordinates per-extractor routing order and merge-aware goal sets (skeleton)."""

    def route_all(self, _ctx: SolverRunContext, _pass2: Pass2Result) -> RoutingResult:
        """Run full STEP4 routing (not implemented)."""
        msg = "MergeAwareRouter.route_all is not implemented (skeleton only)"
        raise NotImplementedError(msg)
