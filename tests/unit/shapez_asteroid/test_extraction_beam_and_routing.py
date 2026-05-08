"""Beam placement rounds / coverage objective."""

from __future__ import annotations

from django_apps.shapez_asteroid.extraction.beam_placement import (
    _default_max_clusters,
    beam_place_clusters,
)
from django_apps.shapez_asteroid.services.asteroid_reconstruction import AsteroidReconstruction


def test_default_max_clusters_scales_with_mineable() -> None:
    assert _default_max_clusters(40) == 4
    assert _default_max_clusters(1000) == 24


def test_beam_can_place_more_than_legacy_eight_clusters() -> None:
    """Previously ``min(max_clusters, 8)`` capped depth; ``max_clusters=12`` must allow >8."""

    cores = [(2 + 4 * i, 2) for i in range(14)]
    mineable = frozenset(cores)
    occupied = mineable
    rec = AsteroidReconstruction(
        blueprint_occupied_cells=occupied,
        extraction_shell_cells=occupied,
        belt_cells=frozenset(),
        pipe_cells=frozenset(),
        legacy_transport_cells=frozenset(),
        interior_patch_cells=frozenset(),
        mineable_placement_cells=mineable,
        x_min=min(c[0] for c in cores),
        x_max=max(c[0] for c in cores),
        y_min=2,
        y_max=2,
    )
    got = beam_place_clusters(rec=rec, beam_width=8, max_clusters=12, time_budget_sec=30.0)
    assert len(got) > 8


def test_beam_place_clusters_calls_on_round() -> None:
    cores = [(2 + 4 * i, 2) for i in range(14)]
    mineable = frozenset(cores)
    occupied = mineable
    rec = AsteroidReconstruction(
        blueprint_occupied_cells=occupied,
        extraction_shell_cells=occupied,
        belt_cells=frozenset(),
        pipe_cells=frozenset(),
        legacy_transport_cells=frozenset(),
        interior_patch_cells=frozenset(),
        mineable_placement_cells=mineable,
        x_min=min(c[0] for c in cores),
        x_max=max(c[0] for c in cores),
        y_min=2,
        y_max=2,
    )
    seen: list[tuple[int, int]] = []

    def on_round(i: int, n: int) -> None:
        seen.append((i, n))

    beam_place_clusters(
        rec=rec,
        beam_width=8,
        max_clusters=12,
        on_round=on_round,
        time_budget_sec=30.0,
    )
    assert len(seen) >= 1
    assert all(t[1] == 12 for t in seen)


def test_beam_place_clusters_respects_max_clusters_one() -> None:
    cores = [(2 + 4 * i, 2) for i in range(14)]
    mineable = frozenset(cores)
    rec = AsteroidReconstruction(
        blueprint_occupied_cells=mineable,
        extraction_shell_cells=mineable,
        belt_cells=frozenset(),
        pipe_cells=frozenset(),
        legacy_transport_cells=frozenset(),
        interior_patch_cells=frozenset(),
        mineable_placement_cells=mineable,
        x_min=min(c[0] for c in cores),
        x_max=max(c[0] for c in cores),
        y_min=2,
        y_max=2,
    )
    got = beam_place_clusters(rec=rec, beam_width=8, max_clusters=1)
    assert len(got) <= 1
