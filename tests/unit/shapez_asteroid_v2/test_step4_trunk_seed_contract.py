"""STEP 4 trunk seed (§9.2) skeleton: must not silently succeed."""

from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.routing.trunk_seed import (
    build_trunk_seed_candidates,
)


def _ctx() -> SolverRunContext:
    return SolverRunContext(run_id="t", reconstruction=ReconstructionDTO())


def test_trunk_seed_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        build_trunk_seed_candidates(_ctx())
