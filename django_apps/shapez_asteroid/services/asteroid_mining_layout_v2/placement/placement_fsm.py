"""
Placement commit state transitions (§9.6).

Lives under ``placement/`` (not v1 ``asteroid_mining_layout``). Domain DTO/enums only;
no replay readers, no routing construction, no Django.
"""

from __future__ import annotations

from dataclasses import replace

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass1Result,
    Pass2Result,
    SolverRunContext,
)
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
        msg = f"illegal placement commit transition {from_state!r} -> {to_state!r}"
        raise ValueError(msg)


def assert_all_provisional_commits(
    entries: tuple[tuple[str, PlacementCommitState], ...],
) -> None:
    """Pass1/Pass2 register ``PROVISIONAL_PLACED`` only until STEP 4 (§7.3, §9.6)."""

    for _pid, st in entries:
        assert_provisionally_placed(st)


def assert_no_routed_confirmed(
    entries: tuple[tuple[str, PlacementCommitState], ...],
) -> None:
    for _pid, st in entries:
        if st is PlacementCommitState.ROUTED_CONFIRMED:
            msg = "ROUTED_CONFIRMED must not appear before STEP 4 routing"
            raise AssertionError(msg)


def apply_pass1_provisional_commits(ctx: SolverRunContext, pass1: Pass1Result) -> SolverRunContext:
    """Merge Pass1 provisional ids into ``ctx.placement_commit_by_id`` (returns new ctx)."""

    if not pass1.placement_commit_entries:
        return ctx
    merged = dict(ctx.placement_commit_by_id)
    for pid, st in pass1.placement_commit_entries:
        merged[pid] = st
    out: SolverRunContext = replace(ctx, placement_commit_by_id=merged)
    return out


def apply_pass2_provisional_commits(ctx: SolverRunContext, pass2: Pass2Result) -> SolverRunContext:
    """Merge Pass2 provisional ids into ``ctx.placement_commit_by_id`` (returns new ctx)."""

    if not pass2.placement_commit_entries:
        return ctx
    merged = dict(ctx.placement_commit_by_id)
    for pid, st in pass2.placement_commit_entries:
        merged[pid] = st
    out: SolverRunContext = replace(ctx, placement_commit_by_id=merged)
    return out


__all__ = [
    "apply_pass1_provisional_commits",
    "apply_pass2_provisional_commits",
    "assert_all_provisional_commits",
    "assert_no_routed_confirmed",
    "assert_placement_commit_transition",
    "assert_provisionally_placed",
    "is_terminal_state",
    "placement_commit_transition_allowed",
]
