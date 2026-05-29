"""Cell hull outline loops — corner lattice geometry (shared by rim + pattern highlight)."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.cell_hull_outline import (
    build_cell_hull_outline_loops,
)


def test_single_cell_hull_is_closed_rectangle() -> None:
    loops = build_cell_hull_outline_loops(frozenset({(1, 0)}))
    assert len(loops) == 1
    loop = loops[0]
    assert len(loop) >= 4
    assert loop[0] == loop[-1]


def test_two_separated_cells_yield_two_loops() -> None:
    loops = build_cell_hull_outline_loops(frozenset({(1, 0), (5, 0)}))
    assert len(loops) == 2


def test_empty_occupied_returns_empty() -> None:
    assert build_cell_hull_outline_loops(frozenset()) == ()


def test_adjacent_cells_share_one_loop() -> None:
    loops = build_cell_hull_outline_loops(frozenset({(1, 0), (2, 0)}))
    assert len(loops) == 1
