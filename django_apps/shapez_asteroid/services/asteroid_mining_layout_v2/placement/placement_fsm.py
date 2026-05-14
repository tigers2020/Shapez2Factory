"""Re-export placement FSM from ``domain`` (canonical §9.6)."""

from __future__ import annotations

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
