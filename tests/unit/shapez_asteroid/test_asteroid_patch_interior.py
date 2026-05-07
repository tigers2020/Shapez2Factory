from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_patch_interior import (
    compute_patch_interior_cells,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import list_island_mining_map


def test_interior_closed_3x3_ring() -> None:
    occupied = {
        (0, 0),
        (1, 0),
        (2, 0),
        (0, 1),
        (2, 1),
        (0, 2),
        (1, 2),
        (2, 2),
    }
    assert compute_patch_interior_cells(occupied) == [(1, 1)]


def test_interior_open_top_bridged_with_default_dilation() -> None:
    """One-cell gap: morphological closing seals the perimeter for the flood barrier."""

    occupied = {
        (0, 0),
        (2, 0),
        (0, 1),
        (2, 1),
        (0, 2),
        (1, 2),
        (2, 2),
    }
    assert compute_patch_interior_cells(occupied) == [(1, 1)]


def test_interior_open_top_stays_open_with_zero_bridge() -> None:
    """Strict mode: missing top-middle lets outside flood into the hole."""

    occupied = {
        (0, 0),
        (2, 0),
        (0, 1),
        (2, 1),
        (0, 2),
        (1, 2),
        (2, 2),
    }
    assert compute_patch_interior_cells(occupied, perimeter_bridge_steps=0) == []


def test_interior_few_cells_returns_empty() -> None:
    assert compute_patch_interior_cells({(0, 0), (1, 0)}) == []


def test_interior_solid_block_no_hole() -> None:
    occupied = {(i, j) for i in range(3) for j in range(3)}
    assert compute_patch_interior_cells(occupied) == []


def test_interior_wide_chamber_keeps_one_cell_thick_core() -> None:
    """Slit-shaped coordinates deep inside are not stripped (only near flood outside)."""

    occupied: set[tuple[int, int]] = set()
    for y in range(1, 6):
        occupied.add((0, y))
        occupied.add((4, y))
    occupied.update(
        {
            (1, 0),
            (2, 0),
            (3, 0),
            (1, 6),
            (2, 6),
            (3, 6),
        }
    )
    interior = compute_patch_interior_cells(occupied)
    assert (2, 3) in interior
    assert len(interior) == 3 * 5  # x=1..3, y=1..5 void


def test_list_island_mining_map_includes_inferred_ring() -> None:
    t = "Layout_ShapeMiner"
    entries = [
        {"X": 10, "Y": 10, "T": t},
        {"X": 11, "Y": 10, "T": t},
        {"X": 12, "Y": 10, "T": t},
        {"X": 10, "Y": 11, "T": t},
        {"X": 12, "Y": 11, "T": t},
        {"X": 10, "Y": 12, "T": t},
        {"X": 11, "Y": 12, "T": t},
        {"X": 12, "Y": 12, "T": t},
    ]
    decoded = {"BP": {"Entries": entries}}
    m = list_island_mining_map(decoded)
    assert {"x": 11, "y": 11, "role": "inferred", "surface": "shape"} in m
    assert sum(1 for c in m if c.get("role") == "occupied") == 8
