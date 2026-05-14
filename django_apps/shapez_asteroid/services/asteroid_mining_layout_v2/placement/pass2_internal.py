"""
Pass2 internal fill placement (STEP 3, §8).

Commits are PROVISIONAL_PLACED only; STEP 4 confirms routes (CANON).
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass1Result,
    Pass2Result,
    SolverRunContext,
)


def run_pass2_internal_fill(_ctx: SolverRunContext, _pass1: Pass1Result) -> Pass2Result:
    """Run Pass2 internal placement (not implemented)."""
    msg = "run_pass2_internal_fill is not implemented (skeleton only)"
    raise NotImplementedError(msg)
