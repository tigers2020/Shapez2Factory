"""Unit tests for orphan island → exterior margin bootstrap (STEP4 pre-stage)."""

from __future__ import annotations

import copy

from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.existing_layout_analysis import (  # noqa: E501
    analyze_existing_layout_from_mining_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.orphan_island_external_bootstrap import (  # noqa: E501
    trunk_seed_hint_count_from_ela,
    try_commit_orphan_island_external_bootstrap,
)


def _is_ext_factory(x0: int):
    def is_ext(c: Coord) -> bool:
        return c[0] >= x0

    return is_ext


def _fluid_field(x: int, y: int) -> dict:
    return {
        "x": x,
        "y": y,
        "role": "inferred",
        "layout_kind": "asteroid_field",
        "surface": "fluid",
    }


def _build_orphan_fluid_island_no_exterior_path() -> tuple[list[dict], list[dict]]:
    """Orphan island in a bounded mineable pocket with no cell adjacent to the exterior shell."""

    rows: list[dict] = []
    for x in range(5, 16):
        for y in range(4, 8):
            rows.append(_fluid_field(x, y))
    for x, y in ((10, 5), (11, 5), (12, 5)):
        rows.append(
            {
                "x": x,
                "y": y,
                "role": "pipe",
                "layout_kind": "fluid_pipe_segment",
                "surface": "fluid",
            }
        )
    rows.append(
        {
            "x": 9,
            "y": 5,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "surface": "fluid",
            "t": "Layout_FluidMiner",
            "r": 0,
        }
    )
    final = copy.deepcopy(rows)
    return rows, final


def _build_orphan_fluid_island_with_corridor() -> tuple[list[dict], list[dict]]:
    """Orphan 3-cell pipe island + corridor to x>=50 exterior."""

    rows: list[dict] = []
    for x in range(5, 50):
        for y in range(4, 8):
            rows.append(_fluid_field(x, y))
    for x, y in ((10, 5), (11, 5), (12, 5)):
        rows.append(
            {
                "x": x,
                "y": y,
                "role": "pipe",
                "layout_kind": "fluid_pipe_segment",
                "surface": "fluid",
            }
        )
    rows.append(
        {
            "x": 9,
            "y": 5,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "surface": "fluid",
            "t": "Layout_FluidMiner",
            "r": 0,
        }
    )
    final = copy.deepcopy(rows)
    return rows, final


def test_orphan_fluid_not_trunk_seed_hint_before_bootstrap() -> None:
    rows, final = _build_orphan_fluid_island_with_corridor()
    is_ext = _is_ext_factory(50)
    ela = analyze_existing_layout_from_mining_map(rows, is_external=is_ext)
    assert ela.get("source_kind") == "existing_fluid_layout"
    assert trunk_seed_hint_count_from_ela(ela) == 0


def test_bootstrap_commits_and_enables_trunk_seed_hint() -> None:
    rows, final = _build_orphan_fluid_island_with_corridor()
    is_ext = _is_ext_factory(50)
    ela0 = analyze_existing_layout_from_mining_map(rows, is_external=is_ext)
    assert trunk_seed_hint_count_from_ela(ela0) == 0

    trace, ela1 = try_commit_orphan_island_external_bootstrap(
        mining_map_rows=rows,
        final_mining_map=final,
        is_external=is_ext,
    )
    assert trace["bootstrap_attempted"] is True
    assert trace["bootstrap_committed"] is True
    assert ela1 is not None
    assert int(trace["external_reachable_transport_before_bootstrap_count"] or 0) == 0
    assert int(trace["external_reachable_transport_after_bootstrap_count"] or 0) > 0
    assert trunk_seed_hint_count_from_ela(ela1) > 0


def test_bootstrap_fails_cleanly_when_no_path() -> None:
    rows, final = _build_orphan_fluid_island_no_exterior_path()
    is_ext = _is_ext_factory(50)
    ela0 = analyze_existing_layout_from_mining_map(rows, is_external=is_ext)
    hint0 = trunk_seed_hint_count_from_ela(ela0)

    trace, ela1 = try_commit_orphan_island_external_bootstrap(
        mining_map_rows=rows,
        final_mining_map=final,
        is_external=is_ext,
    )
    assert trace["bootstrap_committed"] is False
    assert ela1 is None
    assert trace.get("bootstrap_failure_reason") == "geometry_no_path"
    assert trunk_seed_hint_count_from_ela(ela0) == hint0 == 0


def test_bootstrap_does_not_invent_hard_protected_corridors() -> None:
    """Bootstrap mutates transport rows only; no STEP4 ``routing_state`` exists here."""

    rows, final = _build_orphan_fluid_island_with_corridor()
    is_ext = _is_ext_factory(50)
    trace, _ela1 = try_commit_orphan_island_external_bootstrap(
        mining_map_rows=rows,
        final_mining_map=final,
        is_external=is_ext,
    )
    assert trace["bootstrap_committed"] is True
    assert "hard_protected" not in trace
