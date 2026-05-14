from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement.placement_fsm import (
    assert_provisionally_placed,
    is_terminal_state,
)


def test_is_terminal_state() -> None:
    assert is_terminal_state(PlacementCommitState.ROUTED_CONFIRMED) is True
    assert is_terminal_state(PlacementCommitState.ROLLED_BACK) is True
    assert is_terminal_state(PlacementCommitState.PROVISIONAL_PLACED) is False


def test_assert_provisionally_placed_ok() -> None:
    assert_provisionally_placed(PlacementCommitState.PROVISIONAL_PLACED)


def test_assert_provisionally_placed_rejects_routed() -> None:
    with pytest.raises(AssertionError):
        assert_provisionally_placed(PlacementCommitState.ROUTED_CONFIRMED)
