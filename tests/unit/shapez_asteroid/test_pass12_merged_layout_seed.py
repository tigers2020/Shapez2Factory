"""Pass12 merged-map seeding: mineable extractors block Pass1 duplicate placement."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.existing_layout_analysis import (  # noqa: E501
    existing_layout_heuristic_suppress_pass12_loops,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass1_timeline_integration as p12_tl,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.recovery_orchestrator import (  # noqa: E501
    _apply_layout_preserve_hard_gate,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_routing_permission as s4rp,
)


def test_integrate_pass12_seeded_miner_on_mineable_skips_pass1_outer() -> None:
    """Merged map miner on mineable must not be treated as an empty Pass1 slot."""

    fm = [
        {
            "x": 5,
            "y": 5,
            "role": "occupied",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        },
    ]
    wm = [
        {"x": 6, "y": 5, "role": "belt", "surface": "shape"},
        {
            "x": 5,
            "y": 5,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": "shape",
            "t": "Layout_ShapeMiner",
            "r": 0,
        },
    ]
    _m1, _m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm,
        final_mining_map=fm,
        is_external=lambda c: c[0] >= 7,
    )
    assert stats["pass12_preserved_equipment_groups"] == 1
    assert stats["pass1_outer_placements"] == 0
    assert stats["pass1_new_extractor_cells"] == 0


def test_integrate_pass12_extension_facing_across_missing_x0_column() -> None:
    """Extension west of miner can be raw Δx=2 on the no-x0 grid; merge must stay cardinal."""

    y = 3
    fm = [
        {
            "x": -1,
            "y": y,
            "role": "occupied",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        },
        {
            "x": 1,
            "y": y,
            "role": "occupied",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        },
    ]
    wm = [
        {
            "x": -1,
            "y": y,
            "role": "occupied",
            "layout_kind": "extension",
            "surface": "shape",
            "t": "Layout_ShapeMinerExtension",
            "r": 0,
        },
        {
            "x": 1,
            "y": y,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": "shape",
            "t": "Layout_ShapeMiner",
            "r": 0,
        },
        {"x": 2, "y": y, "role": "belt", "surface": "shape"},
    ]
    m1, _m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm,
        final_mining_map=fm,
        is_external=lambda c: c[0] > 10,
    )
    by_xy = {(r["x"], r["y"]): r for r in m1}
    ext = by_xy.get((-1, y))
    assert ext is not None and ext.get("layout_kind") == "extension"
    assert stats["pass12_preserved_routed_placement_records"] >= 1


def test_existing_layout_heuristic_suppress_pass12_loops_true() -> None:
    ela = {
        "source_kind": "existing_shape_layout",
        "equipment": {"miner_count": 2, "extension_count": 1},
        "transport": {"main_component_id": 0},
        "issues": [],
    }
    assert existing_layout_heuristic_suppress_pass12_loops(ela) is True


def test_existing_layout_heuristic_suppress_pass12_loops_raw_false() -> None:
    ela = {
        "source_kind": "raw_asteroid_field",
        "equipment": {"miner_count": 1, "extension_count": 1},
        "transport": {"main_component_id": 0},
        "issues": [],
    }
    assert existing_layout_heuristic_suppress_pass12_loops(ela) is False


def test_step4_step_cost_trunk_reuse_tier() -> None:
    cells = {
        (4, 0): {"x": 4, "y": 0, "role": "belt", "surface": "shape"},
    }
    mineable = frozenset()
    asteroid = frozenset()
    cheap = frozenset({(4, 0)})
    assert (
        s4rp.step4_step_cost(
            (4, 0),
            want_role="belt",
            cells=cells,
            mineable=mineable,
            asteroid=asteroid,
            is_external=lambda _: False,
            cheap_reuse_cells=cheap,
        )
        == 0.5
    )
    assert (
        s4rp.step4_step_cost(
            (4, 0),
            want_role="belt",
            cells=cells,
            mineable=mineable,
            asteroid=asteroid,
            is_external=lambda _: False,
            cheap_reuse_cells=None,
        )
        == 10.0
    )


def test_layout_preserve_hard_gate_restores_timeline_maps() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
        SOLVER_FRAME_PASS3_TRANSPORT,
        SOLVER_FRAME_VALIDATE,
    )

    step05 = [{"x": 1, "y": 0, "role": "belt", "surface": "shape"}]
    out = {
        "solver_timeline": [
            {"id": SOLVER_FRAME_PASS3_TRANSPORT, "mining_map": [{"x": 99, "y": 0}]},
            {"id": SOLVER_FRAME_VALIDATE, "mining_map": [{"x": 99, "y": 0}]},
        ],
        "final_validation": {"optimization_final_internal_transport_count": 50},
    }
    summary_fields: dict = {
        "after_internal_transport_count": 100,
        "optimization_baseline_internal_transport": 10,
        "optimization_warnings": ["internal_transport_above_pass2_baseline"],
    }
    replay: list = []
    _apply_layout_preserve_hard_gate(
        out,
        summary_fields,
        step05_baseline_map=step05,
        existing_layout_analysis={"source_kind": "existing_shape_layout"},
        existing_input_internal_transport=20,
        replay_events=replay,
    )
    assert summary_fields["layout_preserve_hard_gate_triggered"] is True
    assert summary_fields["after_internal_transport_count"] == 20
    assert out["solver_timeline"][0]["mining_map"] == step05
    assert out["final_validation"]["optimization_final_internal_transport_count"] == 20
    assert replay and replay[0]["phase"] == "layout_preserve_hard_gate"


def test_layout_preserve_hard_gate_skipped_for_raw() -> None:
    out = {"solver_timeline": [], "final_validation": {}}
    summary_fields: dict = {"after_internal_transport_count": 999}
    _apply_layout_preserve_hard_gate(
        out,
        summary_fields,
        step05_baseline_map=[],
        existing_layout_analysis={"source_kind": "raw_asteroid_field"},
        existing_input_internal_transport=1,
        replay_events=[],
    )
    assert summary_fields.get("layout_preserve_hard_gate_triggered") is False
    assert summary_fields["after_internal_transport_count"] == 999
