"""STEP4 ``trunk_load`` nested schema + legacy alias contract (v1)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    SOLVER_FRAME_STEP4_ROUTING,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_timeline_integration import (  # noqa: E501
    integrate_pass12_placement_into_working_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    run_step4_merge_aware_routing,
    step4_routing_skipped_result,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_trunk_load import (
    TRUNK_LOAD_CONTRACT_VERSION,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    external_predicate_for_mining_map,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline
from tests.unit.shapez_asteroid.test_step4_merge_routing import (
    _decoded_shape_miners_with_belt_escape,
)


def _assert_trunk_load_nested_matches_legacy(tl: dict) -> None:
    rm = tl["route_metrics"]
    tul = tl["transport_usage_load"]
    assert tl["edges"] == tul["existing_transport_cell_crossings"]
    assert rm["route_cell_visits"] == tl["step4_accumulated_route_cell_visits"]
    assert rm["unique_route_cell_count"] == tl["step4_final_route_cell_count"]
    by_kind = tl["trunk_load_by_kind"]
    assert sum(int(v["route_cell_visits"]) for v in by_kind.values()) == rm["route_cell_visits"]
    assert (
        sum(int(v["unique_route_cell_count"]) for v in by_kind.values())
        == rm["unique_route_cell_count"]
    )


def test_step4_trunk_load_skipped_has_contract_version_and_nested_blocks() -> None:
    r = step4_routing_skipped_result([])
    tl = r.trunk_load
    assert tl["trunk_load_contract_version"] == TRUNK_LOAD_CONTRACT_VERSION == 1
    assert tl["skipped"] is True
    assert tl["route_metrics"]["route_cell_visits"] == 0
    assert tl["route_metrics"]["unique_route_cell_count"] == 0
    assert tl["transport_usage_load"]["existing_transport_cell_crossings"] == {}
    assert tl["transport_usage_load"]["trunk_edge_load"] == {}
    assert "shape_belt" in tl["trunk_load_by_kind"] and "fluid_pipe" in tl["trunk_load_by_kind"]
    _assert_trunk_load_nested_matches_legacy(tl)


def test_step4_trunk_load_keeps_legacy_edges_alias_for_one_release() -> None:
    decoded = _decoded_shape_miners_with_belt_escape()
    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = stats.get("placement_records")
    r = run_step4_merge_aware_routing(
        m2,
        final_mining_map=fm,
        is_external=is_ext,
        placement_records=pr,
    )
    tl = r.trunk_load
    assert tl["trunk_load_contract_version"] == 1
    _assert_trunk_load_nested_matches_legacy(tl)


def test_solver_timeline_step4_frame_summary_includes_full_trunk_load() -> None:
    out = build_solver_timeline(_decoded_shape_miners_with_belt_escape())
    step4_f = next(f for f in out["solver_timeline"] if f["id"] == SOLVER_FRAME_STEP4_ROUTING)
    assert "trunk_load" in step4_f["summary"]
    tl_frame = step4_f["summary"]["trunk_load"]
    tl_ss = out["solver_summary"]["trunk_load"]
    assert tl_frame == tl_ss
    _assert_trunk_load_nested_matches_legacy(tl_frame)
