"""optimization_replay_to_lab_frames adapter (Lab replay contract)."""

from __future__ import annotations

from django_apps.asteroid_lab.services.optimization_replay_to_lab_frames import (
    COMMIT_CLASS_OPTIMIZATION_EVENT_TYPES,
    optimization_replay_frames_to_lab_append_dtos,
)
from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import (
    IncrementalCommitResult,
    OptimizationReplayFrame,
    RouteGoal,
    RouteReservation,
)
from django_apps.shapez_asteroid.optimization.enums import (
    OptimizationReplayEventType,
    ReservationState,
    RouteGoalKind,
    TransportKind,
)


def _goal() -> RouteGoal:
    return RouteGoal(
        coord=Coord(5, 5),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=None,
        priority=1,
        existing_trunk=False,
    )


def test_commit_class_allowlist_is_route_committed_only() -> None:
    assert COMMIT_CLASS_OPTIMIZATION_EVENT_TYPES == frozenset({"route.committed"})


def test_empty_frames_returns_empty_dtos() -> None:
    base = [
        {
            "x": 1,
            "y": 0,
            "layer": 0,
            "cell_kind": "field",
            "transport_kind": "none",
            "tile_type": "",
        }
    ]
    assert optimization_replay_frames_to_lab_append_dtos((), baseline_full_map=base) == []


def test_overlay_event_preserves_full_map_shape() -> None:
    base = [
        {
            "x": 1,
            "y": 0,
            "layer": 0,
            "cell_kind": "field",
            "transport_kind": "none",
            "tile_type": "",
        }
    ]
    fr = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
        title="c",
        description="",
        visible_cells=(Coord(2, 0),),
        overlay_cells=(),
        metrics={"k": 1},
    )
    dtos = optimization_replay_frames_to_lab_append_dtos((fr,), baseline_full_map=list(base))
    assert len(dtos) == 1
    fm = dtos[0].frame_payload.get("full_map") or []
    assert len(fm) == 1
    assert fm[0].get("cell_kind") == "field"


def test_route_committed_merges_path_when_commit_result_matches() -> None:
    base = [
        {
            "x": 1,
            "y": 0,
            "layer": 0,
            "cell_kind": "field",
            "transport_kind": "none",
            "tile_type": "",
        }
    ]
    rid = "c1:route:0"
    fr = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.ROUTE_COMMITTED,
        title="committed",
        description="",
        visible_cells=(),
        overlay_cells=(),
        metrics={"route_reservation_id": rid},
    )
    resv = RouteReservation(
        reservation_id=rid,
        candidate_id="c1",
        transport_kind=TransportKind.SHAPE_BELT,
        path=(Coord(1, 0), Coord(2, 0)),
        reserved_cells=frozenset({Coord(1, 0), Coord(2, 0)}),
        cost=1,
        reached_goal=_goal(),
        goal_priority=1,
        reservation_state=ReservationState.CONFIRMED,
        domain_cell_transitions=(),
    )
    commit = IncrementalCommitResult(
        committed_placements=(),
        route_reservations=(resv,),
        candidate_results=(),
        final_route_domain={},
        confirmed_candidate_count=1,
        rolled_back_candidate_count=0,
    )
    dtos = optimization_replay_frames_to_lab_append_dtos(
        (fr,),
        baseline_full_map=list(base),
        commit_result=commit,
    )
    fm = dtos[0].frame_payload.get("full_map") or []
    by_xy = {(int(r["x"]), int(r["y"])): r for r in fm if isinstance(r, dict)}
    assert (2, 0) in by_xy
    assert by_xy[(2, 0)].get("transport_kind") == "shape_belt"


def test_route_committed_then_overlay_preserves_committed_full_map() -> None:
    """route.committed advances physical map; a later overlay-only frame must not revert it."""
    base = [
        {
            "x": 1,
            "y": 0,
            "layer": 0,
            "cell_kind": "field",
            "transport_kind": "none",
            "tile_type": "",
        }
    ]
    rid = "c1:route:0"
    committed = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.ROUTE_COMMITTED,
        title="committed",
        description="",
        visible_cells=(),
        overlay_cells=(),
        metrics={"route_reservation_id": rid},
    )
    overlay_only = OptimizationReplayFrame(
        frame_index=1,
        event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
        title="after",
        description="",
        visible_cells=(Coord(1, 0),),
        overlay_cells=(),
        metrics={"k": 2},
    )
    resv = RouteReservation(
        reservation_id=rid,
        candidate_id="c1",
        transport_kind=TransportKind.SHAPE_BELT,
        path=(Coord(1, 0), Coord(2, 0)),
        reserved_cells=frozenset({Coord(1, 0), Coord(2, 0)}),
        cost=1,
        reached_goal=_goal(),
        goal_priority=1,
        reservation_state=ReservationState.CONFIRMED,
        domain_cell_transitions=(),
    )
    commit = IncrementalCommitResult(
        committed_placements=(),
        route_reservations=(resv,),
        candidate_results=(),
        final_route_domain={},
        confirmed_candidate_count=1,
        rolled_back_candidate_count=0,
    )
    dtos = optimization_replay_frames_to_lab_append_dtos(
        (committed, overlay_only),
        baseline_full_map=list(base),
        commit_result=commit,
    )
    assert len(dtos) == 2

    fm0 = dtos[0].frame_payload.get("full_map") or []
    by0 = {(int(r["x"]), int(r["y"])): r for r in fm0 if isinstance(r, dict)}
    assert (2, 0) in by0
    assert by0[(2, 0)].get("transport_kind") == "shape_belt"
    assert (1, 0) in by0
    assert by0[(1, 0)].get("cell_kind") == "transport"

    fm1 = dtos[1].frame_payload.get("full_map") or []
    by1 = {(int(r["x"]), int(r["y"])): r for r in fm1 if isinstance(r, dict)}
    assert (2, 0) in by1
    assert by1[(2, 0)].get("transport_kind") == "shape_belt"
    assert by1[(1, 0)].get("cell_kind") == "transport"


def test_candidate_geometry_dict_roles_round_trip_in_cell_overlay() -> None:
    """Lab append DTO merges visible + overlay rows with overlay_role for UI projection."""
    base = [
        {
            "x": 1,
            "y": 0,
            "layer": 0,
            "cell_kind": "field",
            "transport_kind": "none",
            "tile_type": "",
        }
    ]
    stub = {"x": 3, "y": 0, "layer": 0, "overlay_role": "output_stub", "severity": "info"}
    path_cell = {"x": 2, "y": 0, "layer": 0, "overlay_role": "route_path", "severity": "info"}
    fr = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
        title="c",
        description="",
        visible_cells=(Coord(2, 0), stub),
        overlay_cells=(path_cell,),
        metrics={},
    )
    dtos = optimization_replay_frames_to_lab_append_dtos((fr,), baseline_full_map=list(base))
    cells = dtos[0].cell_overlay_json.get("cells") or []
    at_2 = [
        c
        for c in cells
        if isinstance(c, dict) and int(c.get("x", -1)) == 2 and int(c.get("y", -1)) == 0
    ]
    roles_at_2 = [str(c.get("overlay_role") or "") for c in at_2]
    assert "route_path" in roles_at_2
    assert any(str(c.get("cell_kind") or "") == "optimization_overlay" for c in at_2)
    assert any(
        isinstance(c, dict)
        and int(c.get("x", -1)) == 3
        and str(c.get("overlay_role")) == "output_stub"
        for c in cells
    )


def test_overlay_frame_before_commit_matches_baseline_full_map() -> None:
    """Non-commit frame materialized map equals baseline; commit frame then extends it."""
    base = [
        {
            "x": 1,
            "y": 0,
            "layer": 0,
            "cell_kind": "field",
            "transport_kind": "none",
            "tile_type": "",
        }
    ]
    rid = "c1:route:0"
    overlay_first = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
        title="probe",
        description="",
        visible_cells=(Coord(1, 0),),
        overlay_cells=(),
        metrics={"k": 0},
    )
    committed = OptimizationReplayFrame(
        frame_index=1,
        event_type=OptimizationReplayEventType.ROUTE_COMMITTED,
        title="committed",
        description="",
        visible_cells=(),
        overlay_cells=(),
        metrics={"route_reservation_id": rid},
    )
    resv = RouteReservation(
        reservation_id=rid,
        candidate_id="c1",
        transport_kind=TransportKind.SHAPE_BELT,
        path=(Coord(1, 0), Coord(2, 0)),
        reserved_cells=frozenset({Coord(1, 0), Coord(2, 0)}),
        cost=1,
        reached_goal=_goal(),
        goal_priority=1,
        reservation_state=ReservationState.CONFIRMED,
        domain_cell_transitions=(),
    )
    commit = IncrementalCommitResult(
        committed_placements=(),
        route_reservations=(resv,),
        candidate_results=(),
        final_route_domain={},
        confirmed_candidate_count=1,
        rolled_back_candidate_count=0,
    )
    dtos = optimization_replay_frames_to_lab_append_dtos(
        (overlay_first, committed),
        baseline_full_map=list(base),
        commit_result=commit,
    )
    assert len(dtos) == 2
    fm0 = dtos[0].frame_payload.get("full_map") or []
    assert len(fm0) == 1
    assert fm0[0].get("cell_kind") == "field"
    fm1 = dtos[1].frame_payload.get("full_map") or []
    by1 = {(int(r["x"]), int(r["y"])): r for r in fm1 if isinstance(r, dict)}
    assert (2, 0) in by1
    assert by1[(2, 0)].get("transport_kind") == "shape_belt"
