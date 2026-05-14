from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass1Result,
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement.pass1_outer import (
    run_pass1_outer_placement,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement.pass2_internal import (  # noqa: E501
    run_pass2_internal_fill,
)


def _minimal_ctx() -> SolverRunContext:
    return SolverRunContext(
        run_id="test",
        reconstruction=ReconstructionDTO(),
    )


def test_pass1_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        run_pass1_outer_placement(_minimal_ctx(), ReconstructionDTO())


def test_pass2_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        run_pass2_internal_fill(_minimal_ctx(), Pass1Result())
