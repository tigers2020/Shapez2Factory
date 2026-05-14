from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass2Result,
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.routing.merge_aware_router import (  # noqa: E501
    MergeAwareRouter,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.routing.trunk_seed import (
    build_trunk_seed_candidates,
)


def _ctx() -> SolverRunContext:
    return SolverRunContext(run_id="t", reconstruction=ReconstructionDTO())


def test_trunk_seed_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        build_trunk_seed_candidates(_ctx())


def test_merge_aware_router_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        MergeAwareRouter().route_all(_ctx(), Pass2Result())
