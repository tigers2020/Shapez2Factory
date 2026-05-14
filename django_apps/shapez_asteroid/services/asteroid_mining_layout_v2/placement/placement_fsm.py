"""
Placement commit state transitions (§9.6).

MVP policy: ``QUARANTINED_UNROUTED`` is transient inside STEP4 only; orchestrator
must resolve to ``ROUTED_CONFIRMED`` or ``ROLLED_BACK`` before STEP 9 (see ACTIVE plan).
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
)


def is_terminal_state(state: PlacementCommitState) -> bool:
    """Whether placement state cannot change without a new placement id."""
    return state in (PlacementCommitState.ROUTED_CONFIRMED, PlacementCommitState.ROLLED_BACK)


def assert_provisionally_placed(state: PlacementCommitState) -> None:
    """Pass1/Pass2 must leave new bundles in PROVISIONAL_PLACED."""
    if state is not PlacementCommitState.PROVISIONAL_PLACED:
        msg = f"expected PROVISIONAL_PLACED after pass12, got {state!r}"
        raise AssertionError(msg)
