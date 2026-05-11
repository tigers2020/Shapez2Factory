"""Pass12 ``placement_candidate_blocked_count`` (transport-related stub blocks only)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass1_timeline_integration as p12_tl,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
    _placement_candidate_blocked_count_from_pass12,
)


def _row_af(x: int, y: int) -> dict:
    return {
        "x": x,
        "y": y,
        "role": "inferred",
        "layout_kind": "asteroid_field",
        "surface": "shape",
    }


def test_transport_on_stub_increments_blocked_count() -> None:
    """Existing belt on a would-be output stub counts as transport-related block."""

    fm = [_row_af(10, 0), _row_af(11, 0), _row_af(12, 0)]
    wm = [_row_af(10, 0), _row_af(12, 0), {"x": 11, "y": 0, "role": "belt", "surface": "shape"}]
    is_ext = lambda c: c[0] > 20  # noqa: E731
    _m1, _m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm,
        final_mining_map=fm,
        is_external=is_ext,
        existing_layout_analysis=None,
    )
    assert stats["placement_candidate_blocked_count"] >= 1


def test_hard_barrier_stub_does_not_increment_blocked_count() -> None:
    """Pass2 mineable hard barrier skips stub without counting (not transport-related)."""

    fm = [_row_af(5, 5)]
    wm = [dict(r) for r in fm]
    ela = {
        "source_kind": "existing_shape_layout",
        "solver_hints": {
            "trunk_seed_cell_union": [],
            "cleanup_candidate_cell_union": [[5, 5]],
        },
    }
    is_ext = lambda c: c[0] > 20  # noqa: E731
    _m1, _m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm,
        final_mining_map=fm,
        is_external=is_ext,
        existing_layout_analysis=ela,
    )
    assert stats["existing_layout_barrier_cell_count"] == 1
    assert stats["placement_candidate_blocked_count"] == 0


def test_no_route_only_does_not_increment_blocked_count() -> None:
    """Route probe miss alone does not bump transport-block counter."""

    fm = [_row_af(-1, 0)]
    wm = [dict(r) for r in fm]
    is_ext = lambda c: False  # noqa: E731
    _m1, _m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm,
        final_mining_map=fm,
        is_external=is_ext,
    )
    assert stats["placement_candidate_blocked_count"] == 0


def test_build_solver_timeline_summary_and_replay_carry_blocked_count() -> None:
    out = build_solver_timeline(
        {
            "BP": {
                "Entries": [
                    {"X": 10, "Y": 0, "T": "Layout_ShapeMiner"},
                    {"X": 11, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 12, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 13, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 14, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 15, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 16, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 17, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 18, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 19, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 20, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 21, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 22, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 23, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 24, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 25, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 26, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 27, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 28, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                    {"X": 29, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                ]
            }
        }
    )
    summ = out["solver_summary"]
    assert "placement_candidate_blocked_count" in summ
    assert isinstance(summ["placement_candidate_blocked_count"], int)
    om = out["solver_replay"]["optimization_metrics"]
    assert om["placement_candidate_blocked_count"] == summ["placement_candidate_blocked_count"]


def test_placement_candidate_blocked_count_from_pass12_fallback() -> None:
    assert _placement_candidate_blocked_count_from_pass12(None) == 0
    assert _placement_candidate_blocked_count_from_pass12({}) == 0
    assert (
        _placement_candidate_blocked_count_from_pass12({"placement_candidate_blocked_count": 3})
        == 3
    )
    assert (
        _placement_candidate_blocked_count_from_pass12({"placement_candidate_blocked_count": True})
        == 0
    )


def test_explicit_soft_corridor_cell_increments_blocked_count() -> None:
    fm = [_row_af(10, 0), _row_af(11, 0), _row_af(12, 0)]
    wm = [dict(r) for r in fm]
    ela = {
        "source_kind": "existing_shape_layout",
        "solver_hints": {"trunk_seed_cell_union": [], "cleanup_candidate_cell_union": []},
        "pass12_soft_protected_corridor_cells": [[11, 0]],
    }
    is_ext = lambda c: c[0] > 20  # noqa: E731
    _m1, _m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm,
        final_mining_map=fm,
        is_external=is_ext,
        existing_layout_analysis=ela,
    )
    assert stats["placement_candidate_blocked_count"] >= 1
