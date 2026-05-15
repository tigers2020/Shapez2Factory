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


def _ctx() -> SolverRunContext:
    return SolverRunContext(run_id="t", reconstruction=ReconstructionDTO())


def test_merge_aware_router_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        MergeAwareRouter().route_all(_ctx(), Pass2Result())


def test_step4_corridor_recovery_hook_importable() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.routing import (
        step4_corridor_recovery,
    )

    assert hasattr(step4_corridor_recovery, "step4_corridor_opening_recovery")
