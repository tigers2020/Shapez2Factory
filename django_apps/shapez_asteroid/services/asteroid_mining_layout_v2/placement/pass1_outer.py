"""
Pass1 outer-first placement (STEP 2, §7).

Cheap escape probes must not occupy cells as if they were final routes (CANON §7.3).
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass1Result,
    ReconstructionDTO,
    SolverRunContext,
)


def run_pass1_outer_placement(
    _ctx: SolverRunContext,
    _reconstruction: ReconstructionDTO,
) -> Pass1Result:
    """Run Pass1 outer placement (not implemented)."""
    msg = "run_pass1_outer_placement is not implemented (skeleton only)"
    raise NotImplementedError(msg)
