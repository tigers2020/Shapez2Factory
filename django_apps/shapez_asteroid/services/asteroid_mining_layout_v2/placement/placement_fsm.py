"""
Placement commit state transitions (§9.6).

MVP policy: ``QUARANTINED_UNROUTED`` is transient inside STEP4 only; orchestrator
must resolve to ``ROUTED_CONFIRMED`` or ``ROLLED_BACK`` before STEP 9 (see ACTIVE plan).
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
)

_ALLOWED: dict[PlacementCommitState, frozenset[PlacementCommitState]] = {
    PlacementCommitState.PROVISIONAL_PLACED: frozenset(
        {
            PlacementCommitState.ROUTED_CONFIRMED,
            PlacementCommitState.QUARANTINED_UNROUTED,
            PlacementCommitState.ROLLED_BACK,
        }
    ),
    PlacementCommitState.QUARANTINED_UNROUTED: frozenset(
        {
            PlacementCommitState.ROUTED_CONFIRMED,
            PlacementCommitState.ROLLED_BACK,
        }
    ),
    PlacementCommitState.ROLLED_BACK: frozenset(),
    PlacementCommitState.ROUTED_CONFIRMED: frozenset(),
}


def is_terminal_state(state: PlacementCommitState) -> bool:
    """Whether placement state cannot change without a new placement id."""
    return state in (PlacementCommitState.ROUTED_CONFIRMED, PlacementCommitState.ROLLED_BACK)


def assert_provisionally_placed(state: PlacementCommitState) -> None:
    """Pass1/Pass2 must leave new bundles in PROVISIONAL_PLACED."""
    if state is not PlacementCommitState.PROVISIONAL_PLACED:
        msg = f"expected PROVISIONAL_PLACED after pass12, got {state!r}"
        raise AssertionError(msg)


def placement_commit_transition_allowed(
    from_state: PlacementCommitState,
    to_state: PlacementCommitState,
) -> bool:
    """
    FSM (§9.6):
    PROVISIONAL_PLACED -> ROUTED_CONFIRMED | QUARANTINED_UNROUTED | ROLLED_BACK
    QUARANTINED_UNROUTED -> ROUTED_CONFIRMED | ROLLED_BACK
    ROLLED_BACK / ROUTED_CONFIRMED terminal (no outgoing transitions).
    """
    if from_state is to_state:
        return True
    if from_state in (
        PlacementCommitState.ROLLED_BACK,
        PlacementCommitState.ROUTED_CONFIRMED,
    ):
        return False
    allowed = _ALLOWED.get(from_state)
    if allowed is None:
        return False
    return to_state in allowed


def assert_placement_commit_transition(
    from_state: PlacementCommitState,
    to_state: PlacementCommitState,
) -> None:
    if not placement_commit_transition_allowed(from_state, to_state):
        msg = f"illegal placement commit transition {from_state!s} -> {to_state!s}"
        raise ValueError(msg)
