"""STEP4 internal routing DTO builders."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    _build_step4_ctx_state,
)


def _minimal_map() -> list[dict]:
    return [
        {
            "x": 1,
            "y": 1,
            "role": "occupied",
            "layout_kind": "asteroid_field",
        },
    ]


def test_build_step4_ctx_state_empty_jobs() -> None:
    final_map = _minimal_map()
    ctx, state = _build_step4_ctx_state(
        _minimal_map(),
        final_mining_map=final_map,
        is_external=lambda c: c[0] <= 0,
        placement_records=None,
        existing_layout_analysis=None,
        hard_protected_cells=None,
        force_route_attempt_placement_ids=None,
    )
    assert ctx.mineable == frozenset({(1, 1)})
    assert state.jobs == []
    assert state.cells.keys() == {(1, 1)}
