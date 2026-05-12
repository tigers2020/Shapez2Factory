"""STEP4 merge Dijkstra step costs (§9.2)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_routing_permission as s4rp,
)


def _never_external(_: tuple[int, int]) -> bool:
    return False


def test_default_open_void_not_cheaper_than_asteroid_rock() -> None:
    """Regression: uncatalogued open cells must not undercut in-asteroid rock (merge Dijkstra)."""

    cells: dict = {}
    mineable = frozenset({(3, 0)})
    asteroid = frozenset({(2, 0)})
    open_cell = (1, 0)
    rock = (2, 0)
    assert s4rp.step4_step_cost(
        open_cell,
        want_role="belt",
        cells=cells,
        mineable=mineable,
        asteroid=asteroid,
        is_external=_never_external,
    ) == s4rp.step4_step_cost(
        rock,
        want_role="belt",
        cells=cells,
        mineable=mineable,
        asteroid=asteroid,
        is_external=_never_external,
    )
    assert (
        s4rp.step4_step_cost(
            open_cell,
            want_role="belt",
            cells=cells,
            mineable=mineable,
            asteroid=asteroid,
            is_external=_never_external,
        )
        == 60.0
    )
