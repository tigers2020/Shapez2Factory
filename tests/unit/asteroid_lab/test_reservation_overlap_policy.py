"""F0 Tier C — reservation overlap policy (no DB)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    _private_route_cell_overlap,
)
from django_apps.asteroid_lab.optimization.commit.reservation_overlap_policy import (
    build_elcp_base_cells,
    build_reservation_candidate_cells,
    spine_delta_allowed_in_reservation,
)


def test_build_elcp_base_cells_excludes_reused_trunk() -> None:
    base = build_elcp_base_cells(
        branch_cells=((0, 1), (0, 0)),
        new_trunk_cells=((1, 0),),
        reused_trunk_cells=((1, 0), (2, 0)),
    )
    assert base == frozenset({(0, 1), (0, 0), (1, 0)})
    assert (2, 0) not in base


def test_spine_delta_allowed_excludes_cells_not_in_shareable_or_fl06() -> None:
    spine_delta = frozenset({(5, 5), (1, 0)})
    shareable = frozenset({(1, 0)})
    fl06_required = frozenset()
    allowed = spine_delta_allowed_in_reservation(
        spine_delta,
        shareable_trunk_cells=shareable,
        fl06_required_cells=fl06_required,
    )
    assert allowed == frozenset({(1, 0)})


def test_build_reservation_candidate_cells_never_includes_unallowed_spine() -> None:
    stub_aligned = frozenset({(0, 0), (-1, 0)})
    spine_delta = frozenset({(5, 4), (4, 4)})
    shareable = frozenset()
    result = build_reservation_candidate_cells(
        stub_aligned_cells=stub_aligned,
        spine_delta_cells=spine_delta,
        shareable_trunk_cells=shareable,
        fl06_required_cells=stub_aligned,
    )
    assert (4, 4) not in result
    assert (5, 4) not in result
    assert (-1, 0) in result


def test_peer_branch_overlap_is_private_not_shareable() -> None:
    shareable = frozenset({(1, 0)})
    committed = frozenset({(1, 0), (0, 1)})
    reservation = frozenset({(0, 1)})
    private = _private_route_cell_overlap(
        reservation,
        committed,
        shareable_trunk_cells=shareable,
    )
    assert private == frozenset({(0, 1)})


def test_reused_trunk_overlap_empty_when_not_in_reservation_candidate() -> None:
    shareable = frozenset({(1, 0), (2, 0)})
    committed = frozenset({(1, 0), (2, 0)})
    reservation = frozenset({(0, 1)})
    assert (
        _private_route_cell_overlap(
            reservation,
            committed,
            shareable_trunk_cells=shareable,
        )
        == frozenset()
    )
