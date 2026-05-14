"""
Trunk seed and exterior goal hints (STEP 4 §9.2).

Uses STEP 0.5 hints when present; does not import replay NDJSON readers.
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    SolverRunContext,
)


def build_trunk_seed_candidates(_ctx: SolverRunContext) -> frozenset[tuple[int, int]]:
    """Return candidate trunk seed cells for the current kind-specific routing pass."""
    msg = "build_trunk_seed_candidates is not implemented (skeleton only)"
    raise NotImplementedError(msg)
