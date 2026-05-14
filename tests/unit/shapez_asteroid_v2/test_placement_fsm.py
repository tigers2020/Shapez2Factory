from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass1Result,
    Pass2Result,
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.placement_fsm import (
    apply_pass1_provisional_commits,
    apply_pass2_provisional_commits,
    assert_all_provisional_commits,
    assert_no_routed_confirmed,
    assert_placement_commit_transition,
    assert_provisionally_placed,
    is_terminal_state,
    placement_commit_transition_allowed,
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


@pytest.mark.parametrize(
    ("frm", "to"),
    [
        (
            PlacementCommitState.PROVISIONAL_PLACED,
            PlacementCommitState.ROUTED_CONFIRMED,
        ),
        (
            PlacementCommitState.PROVISIONAL_PLACED,
            PlacementCommitState.QUARANTINED_UNROUTED,
        ),
        (
            PlacementCommitState.PROVISIONAL_PLACED,
            PlacementCommitState.ROLLED_BACK,
        ),
        (
            PlacementCommitState.QUARANTINED_UNROUTED,
            PlacementCommitState.ROUTED_CONFIRMED,
        ),
        (
            PlacementCommitState.QUARANTINED_UNROUTED,
            PlacementCommitState.ROLLED_BACK,
        ),
    ],
)
def test_legal_transitions(
    frm: PlacementCommitState,
    to: PlacementCommitState,
) -> None:
    assert placement_commit_transition_allowed(frm, to) is True
    assert_placement_commit_transition(frm, to)


def test_identity_transition_always_ok() -> None:
    for s in PlacementCommitState:
        assert placement_commit_transition_allowed(s, s) is True


def test_rolled_back_cannot_leave() -> None:
    assert (
        placement_commit_transition_allowed(
            PlacementCommitState.ROLLED_BACK,
            PlacementCommitState.PROVISIONAL_PLACED,
        )
        is False
    )
    with pytest.raises(ValueError, match="illegal placement commit transition"):
        assert_placement_commit_transition(
            PlacementCommitState.ROLLED_BACK,
            PlacementCommitState.ROUTED_CONFIRMED,
        )


def test_routed_confirmed_cannot_regress() -> None:
    assert (
        placement_commit_transition_allowed(
            PlacementCommitState.ROUTED_CONFIRMED,
            PlacementCommitState.QUARANTINED_UNROUTED,
        )
        is False
    )


def test_quarantine_cannot_revert_to_provisional() -> None:
    assert (
        placement_commit_transition_allowed(
            PlacementCommitState.QUARANTINED_UNROUTED,
            PlacementCommitState.PROVISIONAL_PLACED,
        )
        is False
    )


def test_apply_pass1_provisional_commits() -> None:
    ctx = SolverRunContext(run_id="t", reconstruction=ReconstructionDTO())
    p1 = Pass1Result(
        placement_commit_entries=(("a", PlacementCommitState.PROVISIONAL_PLACED),),
    )
    merged = apply_pass1_provisional_commits(ctx, p1)
    assert merged.placement_commit_by_id["a"] is PlacementCommitState.PROVISIONAL_PLACED


def test_assert_all_provisional_commits_pass1_tuple() -> None:
    entries = (("x", PlacementCommitState.PROVISIONAL_PLACED),)
    assert_all_provisional_commits(entries)


def test_apply_pass2_provisional_commits() -> None:
    ctx = SolverRunContext(run_id="t", reconstruction=ReconstructionDTO())
    p2 = Pass2Result(
        placement_commit_entries=(("b", PlacementCommitState.PROVISIONAL_PLACED),),
    )
    merged = apply_pass2_provisional_commits(ctx, p2)
    assert merged.placement_commit_by_id["b"] is PlacementCommitState.PROVISIONAL_PLACED


def test_assert_no_routed_confirmed_rejects_routed() -> None:
    with pytest.raises(AssertionError, match="ROUTED_CONFIRMED"):
        assert_no_routed_confirmed(
            (("x", PlacementCommitState.ROUTED_CONFIRMED),),
        )
