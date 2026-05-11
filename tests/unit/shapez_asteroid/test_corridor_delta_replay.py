"""Replay v7: protected corridor delta payload helpers."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    CORRIDOR_REPLAY_TIERS,
    corridor_added_replay_payload,
    corridor_promoted_replay_payload,
    corridor_removed_replay_payload,
    corridor_replaced_replay_payload,
    sorted_corridor_replay_cells,
)


def test_sorted_corridor_replay_cells_dedupes_sorts_filters_x_zero() -> None:
    raw = [[3, 1], [2, 0], [0, 5], [3, 1], [2, 0]]
    assert sorted_corridor_replay_cells(raw) == [[2, 0], [3, 1]]


def test_sorted_corridor_replay_cells_empty_on_bad_input() -> None:
    assert sorted_corridor_replay_cells(None) == []
    assert sorted_corridor_replay_cells("x") == []


def test_corridor_added_replay_payload_rejects_bad_tier() -> None:
    assert (
        corridor_added_replay_payload(
            transaction_id="t1",
            parent_txn_id=None,
            tier="bogus",
            cells_raw=[[1, 2]],
        )
        is None
    )


def test_corridor_added_replay_payload_none_when_no_cells() -> None:
    assert (
        corridor_added_replay_payload(
            transaction_id="t1",
            parent_txn_id="p",
            tier="hard",
            cells_raw=[],
        )
        is None
    )


def test_corridor_added_replay_payload_shape() -> None:
    pl = corridor_added_replay_payload(
        transaction_id="tid",
        parent_txn_id="pid",
        tier="soft",
        cells_raw=[[5, 1], [4, 2]],
    )
    assert pl is not None
    assert pl["transaction_id"] == "tid"
    assert pl["parent_txn_id"] == "pid"
    assert pl["tier"] == "soft"
    assert pl["cells"] == [[5, 1], [4, 2]]


def test_corridor_removed_matches_added_shape() -> None:
    pl = corridor_removed_replay_payload(
        transaction_id="a",
        parent_txn_id=None,
        tier="candidate",
        cells_raw=[[10, 0]],
    )
    assert pl is not None
    assert pl["tier"] == "candidate"
    assert pl["cells"] == [[10, 0]]


def test_corridor_promoted_replay_payload() -> None:
    assert (
        corridor_promoted_replay_payload(
            transaction_id="t",
            parent_txn_id=None,
            from_tier="soft",
            to_tier="soft",
            cells_raw=[[1, 1]],
        )
        is None
    )
    pl = corridor_promoted_replay_payload(
        transaction_id="t",
        parent_txn_id=None,
        from_tier="candidate",
        to_tier="soft",
        cells_raw=[[2, 3]],
    )
    assert pl is not None
    assert pl["from_tier"] == "candidate"
    assert pl["to_tier"] == "soft"
    assert pl["cells"] == [[2, 3]]


def test_corridor_replaced_replay_payload() -> None:
    assert (
        corridor_replaced_replay_payload(
            transaction_id="t",
            parent_txn_id=None,
            tier="hard",
            cells_removed_raw=[],
            cells_added_raw=[],
        )
        is None
    )
    pl = corridor_replaced_replay_payload(
        transaction_id="p4",
        parent_txn_id="s4",
        tier="soft",
        cells_removed_raw=[[1, 0], [2, 0]],
        cells_added_raw=[[3, 0]],
    )
    assert pl is not None
    assert pl["tier"] == "soft"
    assert pl["cells_removed"] == [[1, 0], [2, 0]]
    assert pl["cells_added"] == [[3, 0]]
    assert pl["parent_txn_id"] == "s4"


def test_corridor_replay_tiers_frozen() -> None:
    assert CORRIDOR_REPLAY_TIERS == frozenset({"hard", "soft", "candidate"})
