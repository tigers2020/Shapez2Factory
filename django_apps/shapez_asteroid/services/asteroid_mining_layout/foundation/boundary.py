"""Rock perimeter helpers for mining layout routing."""

from __future__ import annotations

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4


def cells_touching_void(asteroid_cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    """Asteroid cells with at least one cardinal neighbor outside the asteroid."""

    touch: set[tuple[int, int]] = set()
    for x, y in asteroid_cells:
        for nx, ny in neighbors4(x, y):
            if (nx, ny) not in asteroid_cells:
                touch.add((x, y))
                break
    return touch
