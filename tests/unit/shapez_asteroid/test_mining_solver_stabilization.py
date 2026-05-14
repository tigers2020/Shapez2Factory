"""Stabilization-P0/P1: solver_summary once, validation, route probe."""

from __future__ import annotations

import json
import os
from unittest.mock import patch

import pytest
from django.test import override_settings

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    SOLVER_REPLAY_CONTRACT_VERSION,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit import (  # noqa: E501
    Pass12BundleCandidate,
    Pass12LayoutScratch,
    snapshot_pass12_scratch,
    try_commit_pass1_bundle,
    try_commit_pass2_bundle,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_route_probe import (  # noqa: E501
    bundle_route_probe_or_reject,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.route_probe import (
    probe_stub_cheap_escape_to_external,
    probe_stub_to_external,
    probe_stub_to_external_detail,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    SolverMutationEventKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    _prune_var_logging_files,
    emit_solver_summary_once,
    trace_event,
    trace_run_id_current,
    trace_run_scope,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    FinalValidationReport,
    validate_final_mining_layout,
)


def test_emit_solver_summary_second_call_is_ignored() -> None:
    calls: list[str] = []

    def fake_trace_event(location: str, message: str, data: dict | None = None) -> None:
        calls.append(message)

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace.trace_event",
        fake_trace_event,
    ):
        with trace_run_scope():
            assert emit_solver_summary_once("test", {"run_id": "a", "return_reason": "ok"})
            assert not emit_solver_summary_once("test", {"run_id": "a", "return_reason": "dup"})
    assert calls.count("solver_summary") == 1


def test_run_end_debug_action_includes_solver_summary_snapshot(
    tmp_path, monkeypatch, settings
) -> None:
    """``run_end`` NDJSON row may embed a small ``solver_summary`` snapshot after emit."""

    settings.BASE_DIR = tmp_path
    monkeypatch.setenv("SHAPEZ_SOLVER_ALGO_DEBUG", "1")
    with trace_run_scope():
        rid = trace_run_id_current()
        assert rid is not None
        emit_solver_summary_once(
            "tests.unit.shapez_asteroid.test_mining_solver_stabilization",
            {
                "trace_frame_counter_glossary": {"k": "v"},
                "map_timeline_frame_count": 4,
                "replay_event_count": 2,
            },
        )
        run_path = tmp_path / "var" / "asteroid_mining_layout_debug" / f"{rid}.ndjson"
    assert run_path.exists()
    records = [json.loads(line) for line in run_path.read_text(encoding="utf-8").splitlines()]
    end = next(r for r in records if r.get("action") == "run_end")
    ss = end["data"].get("solver_summary")
    assert isinstance(ss, dict)
    assert "trace_frame_counter_glossary" in ss
    assert ss.get("map_timeline_frame_count") == 4


def test_trace_event_writes_replay_ndjson_and_debug_action_only(
    tmp_path, monkeypatch, settings
) -> None:
    settings.BASE_DIR = tmp_path
    monkeypatch.setenv("SHAPEZ_SOLVER_ALGO_DEBUG", "1")

    with trace_run_scope():
        run_id = trace_run_id_current()
        trace_event("test.location", "test_message", {"value": 3})

    assert run_id is not None
    debug_dir = tmp_path / "var" / "asteroid_mining_layout_debug"
    replay_dir = tmp_path / "var" / "asteroid_mining_layout_replay"
    run_path = debug_dir / f"{run_id}.ndjson"
    latest_path = debug_dir / "latest.ndjson"
    replay_run = replay_dir / f"{run_id}.ndjson"
    replay_latest = replay_dir / "replay_latest.ndjson"
    assert run_path.exists()
    assert latest_path.exists()
    assert replay_run.exists()
    assert replay_latest.exists()

    records = [json.loads(line) for line in run_path.read_text(encoding="utf-8").splitlines()]
    assert [r["action"] for r in records if r.get("kind") == "action"] == [
        "run_start",
        "run_end",
    ]
    start = next(r for r in records if r.get("action") == "run_start")
    assert "debug_session" in start["data"]
    end = next(r for r in records if r.get("action") == "run_end")
    assert "elapsed_s" in end["data"]
    assert not [r for r in records if r.get("kind") == "trace"]

    wire = [json.loads(line) for line in replay_run.read_text(encoding="utf-8").splitlines()]
    assert len(wire) == 1
    assert wire[0]["location"] == "test.location"
    assert wire[0]["message"] == "test_message"
    assert wire[0]["data"]["value"] == 3
    assert latest_path.read_text(encoding="utf-8") == run_path.read_text(encoding="utf-8")
    assert replay_latest.read_text(encoding="utf-8") == replay_run.read_text(encoding="utf-8")


def test_prune_var_logs_drop_oldest_from_ten_ndjson(tmp_path, settings) -> None:
    settings.BASE_DIR = tmp_path
    var_debug = tmp_path / "var" / "asteroid_mining_layout_debug"
    var_debug.mkdir(parents=True)
    base_t = 1_700_000_000.0
    for i in range(10):
        path = var_debug / f"run{i:02d}.ndjson"
        path.write_text("{}", encoding="utf-8")
        t = base_t + float(i)
        os.utime(path, (t, t))

    _prune_var_logging_files()

    names = sorted(p.name for p in var_debug.glob("*.ndjson"))
    assert len(names) == 9
    assert "run00.ndjson" not in names
    assert "run09.ndjson" in names


def test_validate_overlap_miner_and_belt_same_cell_invalid() -> None:
    mining_map = [
        {
            "x": 5,
            "y": 5,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "miner",
            "t": "Layout_ShapeMiner",
        },
        {"x": 5, "y": 5, "role": "belt", "surface": "shape"},
    ]
    r = validate_final_mining_layout(mining_map)
    assert isinstance(r, FinalValidationReport)
    assert r.overlap_violation_count >= 1
    assert not r.geometry_valid


def test_probe_stub_reaches_external_neighbor() -> None:
    transport = frozenset({(2, 0), (3, 0), (4, 0)})
    blocked = frozenset({(1, 0)})
    is_ext = lambda c: c == (5, 0)  # noqa: E731

    assert probe_stub_to_external(
        stub_cell=(2, 0),
        transport_cells=transport,
        blocked_cells=blocked,
        is_external=is_ext,
    )


def test_probe_stub_dead_end() -> None:
    transport = frozenset({(2, 0), (3, 0)})
    blocked: frozenset[tuple[int, int]] = frozenset()
    is_ext = lambda c: c[0] >= 10  # noqa: E731

    assert not probe_stub_to_external(
        stub_cell=(2, 0),
        transport_cells=transport,
        blocked_cells=blocked,
        is_external=is_ext,
    )
    ok, detail = probe_stub_to_external_detail(
        stub_cell=(2, 0),
        transport_cells=transport,
        blocked_cells=blocked,
        is_external=is_ext,
    )
    assert not ok
    assert detail["transport_probe"]["reachable_cells_in_component"] == 2


def test_probe_cheap_escape_void_reaches_external_when_transport_only_dead_end() -> None:
    transport = frozenset({(1, 0)})
    blocked = frozenset({(-1, 0)})
    is_ext = lambda c: c[0] > 5  # noqa: E731

    assert not probe_stub_to_external(
        stub_cell=(1, 0),
        transport_cells=transport,
        blocked_cells=blocked,
        is_external=is_ext,
    )
    assert probe_stub_cheap_escape_to_external(
        stub_cell=(1, 0),
        transport_cells=transport,
        blocked_cells=blocked,
        is_external=is_ext,
        allowed_void_cells=frozenset((x, 0) for x in range(-5, 16) if x != 0),
    )


def test_bundle_route_pass1_cheap_escape_succeeds_without_transport_path() -> None:
    transport = frozenset({(1, 0)})
    blocked = frozenset({(-1, 0)})
    is_ext = lambda c: c[0] > 5  # noqa: E731
    assert bundle_route_probe_or_reject(
        (1, 0),
        transport_cells=transport,
        blocked_cells=blocked,
        is_external=is_ext,
        trace_location="test.p1",
        pass1_allow_cheap_escape=True,
        p1_cheap_void_cells=frozenset((x, 0) for x in range(-5, 16) if x != 0),
    )


def test_bundle_route_without_cheap_fails_when_only_void_path_exists() -> None:
    transport = frozenset({(1, 0)})
    blocked = frozenset({(-1, 0)})
    is_ext = lambda c: c[0] > 5  # noqa: E731
    rejected: list[dict] = []

    def capture_reject(loc: str, data: dict | None) -> None:
        rejected.append({"loc": loc, "data": data or {}})

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_route_probe."
        "trace_bundle_reject_no_route",
        capture_reject,
    ):
        ok = bundle_route_probe_or_reject(
            (1, 0),
            transport_cells=transport,
            blocked_cells=blocked,
            is_external=is_ext,
            trace_location="test.pass2",
            pass1_allow_cheap_escape=False,
        )
    assert not ok
    assert rejected


def test_bundle_route_probe_or_reject_traces_failure() -> None:
    rejected: list[dict] = []

    def capture_reject(loc: str, data: dict | None) -> None:
        rejected.append({"loc": loc, "data": data or {}})

    transport = frozenset({(2, 0)})
    blocked: frozenset[tuple[int, int]] = frozenset()
    is_ext = lambda c: c[0] >= 100  # noqa: E731

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_route_probe."
        "trace_bundle_reject_no_route",
        capture_reject,
    ):
        ok = bundle_route_probe_or_reject(
            (2, 0),
            transport_cells=transport,
            blocked_cells=blocked,
            is_external=is_ext,
            trace_location="test.bundle",
            bundle_hint={"bid": "x"},
        )
    assert not ok
    assert rejected and rejected[0]["loc"] == "test.bundle"
    payload = rejected[0]["data"]
    assert payload["transport_probe"]["failure"] == "no_transport_path_to_external"
    assert payload["cheap_escape_probe"]["skipped"] is True
    assert "route_probe_context" in payload


def test_build_solver_timeline_empty_bp() -> None:
    decoded: dict = {"BP": {"Entries": []}}
    out = build_solver_timeline(decoded)
    assert out["return_reason"] == "ok"
    assert out["solver_termination"] == "success"
    assert out["termination"]["tier"] == "SUCCESS"
    assert out["termination"]["ok"] is True
    assert out["solver_summary"]["solver_termination"] == "success"
    assert out["solver_summary"]["termination"]["tier"] == "SUCCESS"
    assert out["solver_summary"]["capacity_mode"] == "accumulate_only"
    assert out["solver_summary"]["geometry_valid"] is True


def test_build_solver_timeline_replay_v3_emits_step4_transaction_events() -> None:
    decoded: dict = {
        "BP": {
            "Entries": [{"X": x, "Y": 0, "T": "Layout_ShapeMiner"} for x in range(10, 13)]
            + [{"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0} for x in range(13, 30)]
        }
    }
    out = build_solver_timeline(decoded)
    sr = out["solver_replay"]
    assert sr["contract_version"] == SOLVER_REPLAY_CONTRACT_VERSION
    assert isinstance(sr.get("ui_frames"), list)
    assert sr.get("computation_cycle") == len(sr["events"])
    for ev in sr["events"]:
        assert isinstance(ev, dict)
        assert isinstance(ev.get("computation_cycle"), int)
    assert isinstance(sr["events"], list)
    kinds = [e.get("kind") for e in sr["events"]]
    assert SolverMutationEventKind.TRANSACTION_BEGIN.value in kinds
    assert SolverMutationEventKind.MAP_DIFF_COMMITTED.value in kinds
    assert SolverMutationEventKind.CORRIDOR_ADDED.value in kinds
    snap_kinds = [
        e.get("kind") for e in sr["events"] if isinstance(e, dict) and e.get("phase") == "pass3"
    ]
    assert SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value in snap_kinds
    markers: list[str] = []
    for e in sr["events"]:
        if not isinstance(e, dict):
            continue
        if e.get("kind") != SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value:
            continue
        pl = e.get("payload")
        if isinstance(pl, dict) and isinstance(pl.get("marker"), str):
            markers.append(pl["marker"])
    assert "before" in markers and "after" in markers
    p3_tid: str | None = None
    for e in sr["events"]:
        if not isinstance(e, dict) or e.get("phase") != "pass3":
            continue
        if e.get("kind") != SolverMutationEventKind.TRANSACTION_BEGIN.value:
            continue
        pl = e.get("payload")
        if isinstance(pl, dict) and isinstance(pl.get("transaction_id"), str):
            p3_tid = pl["transaction_id"]
            break
    assert p3_tid
    for e in sr["events"]:
        if not isinstance(e, dict) or e.get("phase") != "pass3":
            continue
        pl = e.get("payload")
        if not isinstance(pl, dict):
            continue
        tid = pl.get("transaction_id")
        if tid is not None:
            assert tid == p3_tid
    step4_txn: list[str] = []
    for e in sr["events"]:
        if not isinstance(e, dict) or e.get("phase") != "step4":
            continue
        pl = e.get("payload")
        if not isinstance(pl, dict):
            continue
        tid = pl.get("transaction_id")
        if e.get("kind") in (
            SolverMutationEventKind.TRANSACTION_BEGIN.value,
            SolverMutationEventKind.ROLLBACK.value,
            SolverMutationEventKind.MAP_DIFF_COMMITTED.value,
        ):
            assert isinstance(tid, str) and len(tid) >= 8
            step4_txn.append(tid)
    assert len(step4_txn) >= 2
    assert len(set(step4_txn)) == 1


def test_build_solver_timeline_replay_parent_txn_pass12_to_step4_to_p4() -> None:
    """pass12 txn is parent of step4; step4 txn is parent of p4 when P4 runs."""

    decoded: dict = {
        "BP": {
            "Entries": [{"X": x, "Y": 0, "T": "Layout_ShapeMiner"} for x in range(10, 13)]
            + [{"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0} for x in range(13, 30)]
        }
    }
    out = build_solver_timeline(decoded)
    events = out["solver_replay"]["events"]
    pass12_tid: str | None = None
    step4_tid: str | None = None
    for e in events:
        if not isinstance(e, dict):
            continue
        pl = e.get("payload")
        if not isinstance(pl, dict):
            continue
        tid = pl.get("transaction_id")
        if not isinstance(tid, str):
            continue
        if (
            e.get("phase") == "pass12"
            and e.get("kind") == SolverMutationEventKind.MAP_DIFF_COMMITTED.value
        ):
            pass12_tid = tid
        if (
            e.get("phase") == "step4"
            and e.get("kind") == SolverMutationEventKind.TRANSACTION_BEGIN.value
        ):
            step4_tid = tid
            assert pl.get("parent_txn_id") == pass12_tid
    assert pass12_tid and step4_tid
    pass3_begin = next(
        (
            e
            for e in events
            if isinstance(e, dict)
            and e.get("phase") == "pass3"
            and e.get("kind") == SolverMutationEventKind.TRANSACTION_BEGIN.value
        ),
        None,
    )
    if pass3_begin is not None:
        pl3 = pass3_begin.get("payload")
        assert isinstance(pl3, dict)
        assert pl3.get("parent_txn_id") == step4_tid
    p4_begins = [
        e
        for e in events
        if isinstance(e, dict)
        and e.get("phase") == "p4_reclaim"
        and e.get("kind") == SolverMutationEventKind.TRANSACTION_BEGIN.value
    ]
    if p4_begins:
        pl4 = p4_begins[0].get("payload")
        assert isinstance(pl4, dict)
        assert pl4.get("parent_txn_id") == step4_tid


def test_build_solver_timeline_ui_frames_align_with_timeline() -> None:
    """``solver_replay.ui_frames``는 ``solver_timeline`` 길이·id와 정렬된다."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
        SOLVER_FRAME_PASS3_TRANSPORT,
        SOLVER_TIMELINE_FRAME_ORDER,
    )

    decoded: dict = {
        "BP": {
            "Entries": [{"X": x, "Y": 0, "T": "Layout_ShapeMiner"} for x in range(10, 13)]
            + [{"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0} for x in range(13, 30)]
        }
    }
    out = build_solver_timeline(decoded)
    tl = out["solver_timeline"]
    ui = out["solver_replay"]["ui_frames"]
    ss = out.get("solver_summary") or {}
    assert isinstance(ss.get("solver_timeline_frame_count"), int)
    assert ss["solver_timeline_frame_count"] == len(tl)
    assert isinstance(ss.get("map_timeline_frame_count"), int)
    assert "replay_frame_count" in ss and "replay_event_count" in ss
    assert len(ui) == len(tl) == len(SOLVER_TIMELINE_FRAME_ORDER)
    for i, row in enumerate(ui):
        assert row["timeline_index"] == i
        assert row["timeline_frame_id"] == tl[i].get("id")
    p3_row = next(r for r in ui if r["timeline_frame_id"] == SOLVER_FRAME_PASS3_TRANSPORT)
    assert isinstance(p3_row.get("pass3_layout_snapshots"), list)
    markers = [s["marker"] for s in p3_row["pass3_layout_snapshots"] if "marker" in s]
    assert "before" in markers and "after" in markers
    assert tl[-1]["mining_map"] == tl[-2]["mining_map"]


def test_build_solver_timeline_summary_preserves_routing_state_shape() -> None:
    """STEP4 protected corridor pool shape는 solver_summary까지 보존한다."""

    decoded: dict = {
        "BP": {
            "Entries": [{"X": x, "Y": 0, "T": "Layout_ShapeMiner"} for x in range(10, 13)]
            + [{"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0} for x in range(13, 30)]
        }
    }
    out = build_solver_timeline(decoded)
    routing_state = out["solver_summary"]["routing_state"]
    assert isinstance(routing_state, dict)
    assert isinstance(routing_state.get("hard_protected_corridors"), list)
    assert isinstance(routing_state.get("soft_protected_corridors"), list)
    protected_corridors = routing_state.get("protected_corridors")
    assert isinstance(protected_corridors, dict)
    assert isinstance(protected_corridors.get("hard"), list)
    assert isinstance(protected_corridors.get("soft"), list)


def test_pass1_reject_leaves_no_transport_or_blocked_residue() -> None:
    st = Pass12LayoutScratch(transport_cells={(10, 0)}, blocked_cells={(1, 0)})
    before_t, before_b = set(st.transport_cells), set(st.blocked_cells)
    before_x, before_e = set(st.extractor_cells), dict(st.extension_facings)
    before_od = dict(st.extractor_output_dirs)
    cand = Pass12BundleCandidate(
        blocked_cells=frozenset({(8, 0)}),
        new_transport=frozenset({(2, 0), (3, 0)}),
        stub_cell=(2, 0),
    )
    is_ext = lambda c: c[0] >= 20  # noqa: E731
    assert not try_commit_pass1_bundle(st, cand, is_external=is_ext)
    assert st.transport_cells == before_t
    assert st.blocked_cells == before_b
    assert st.extractor_cells == before_x
    assert st.extension_facings == before_e
    assert st.extractor_output_dirs == before_od


def test_pass1_bundle_probe_exception_restores_full_scratch() -> None:
    st = Pass12LayoutScratch(transport_cells={(10, 0)}, blocked_cells={(1, 0)})
    before = snapshot_pass12_scratch(st)
    cand = Pass12BundleCandidate(
        blocked_cells=frozenset({(8, 0)}),
        new_transport=frozenset({(2, 0), (3, 0)}),
        stub_cell=(2, 0),
    )
    is_ext = lambda c: c[0] >= 5  # noqa: E731
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit."
        "bundle_route_probe_or_reject",
        side_effect=RuntimeError("probe boom"),
    ):
        with pytest.raises(RuntimeError, match="probe boom"):
            try_commit_pass1_bundle(st, cand, is_external=is_ext)
    assert snapshot_pass12_scratch(st) == before


def test_pass1_commit_applies_delta_when_route_exists() -> None:
    st = Pass12LayoutScratch(transport_cells=set(), blocked_cells={(1, 0)})
    cand = Pass12BundleCandidate(
        blocked_cells=frozenset({(9, 0)}),
        new_transport=frozenset({(2, 0), (3, 0), (4, 0)}),
        stub_cell=(2, 0),
    )
    is_ext = lambda c: c[0] >= 5 and c[1] == 0  # noqa: E731
    assert try_commit_pass1_bundle(st, cand, is_external=is_ext)
    assert (2, 0) in st.transport_cells and (9, 0) in st.blocked_cells


def test_pass1_reject_emits_bundle_reject_no_route() -> None:
    rejected: list[str] = []

    def capture_reject(loc: str, data: dict | None) -> None:
        rejected.append(loc)

    st = Pass12LayoutScratch(transport_cells={(10, 0)}, blocked_cells=set())
    cand = Pass12BundleCandidate(
        blocked_cells=frozenset({(8, 0)}),
        new_transport=frozenset({(2, 0)}),
        stub_cell=(2, 0),
    )
    is_ext = lambda c: c[0] >= 100  # noqa: E731
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_route_probe."
        "trace_bundle_reject_no_route",
        capture_reject,
    ):
        assert not try_commit_pass1_bundle(st, cand, is_external=is_ext)
    assert rejected == ["pass12_bundle_commit.try_commit_pass1_bundle"]


def test_pass1_invalid_stub_emits_bundle_reject_invalid_stub() -> None:
    invalid_calls: list[str] = []

    def capture_invalid(loc: str, data: dict | None) -> None:
        invalid_calls.append(loc)

    st = Pass12LayoutScratch(transport_cells=set(), blocked_cells=set())
    cand = Pass12BundleCandidate(
        blocked_cells=frozenset({(9, 0)}),
        new_transport=frozenset({(2, 0), (3, 0)}),
        stub_cell=(5, 0),
    )
    is_ext = lambda c: True  # noqa: E731
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit."
        "trace_bundle_reject_invalid_stub",
        capture_invalid,
    ):
        assert not try_commit_pass1_bundle(st, cand, is_external=is_ext)
    assert invalid_calls == ["pass12_bundle_commit.try_commit_pass1_bundle"]
    assert st.transport_cells == set() and st.blocked_cells == set()


def test_pass2_commit_uses_pass2_trace_location() -> None:
    locations: list[str] = []

    def spy_probe(
        stub_cell: tuple[int, int],
        *,
        transport_cells: frozenset[tuple[int, int]],
        blocked_cells: frozenset[tuple[int, int]],
        is_external,
        trace_location: str,
        bundle_hint: dict | None = None,
        pass1_allow_cheap_escape: bool = False,
        p1_cheap_void_cells: frozenset[tuple[int, int]] | None = None,
        pass2_adjacent_preserve_trunk_baseline_cells: frozenset[tuple[int, int]] | None = None,
    ) -> bool:
        locations.append(trace_location)
        return True

    st = Pass12LayoutScratch()
    cand = Pass12BundleCandidate(
        blocked_cells=frozenset({(9, 0)}),
        new_transport=frozenset({(2, 0), (3, 0)}),
        stub_cell=(2, 0),
    )
    is_ext = lambda c: True  # noqa: E731
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit."
        "bundle_route_probe_or_reject",
        spy_probe,
    ):
        assert try_commit_pass2_bundle(st, cand, is_external=is_ext)
    assert locations == ["pass12_bundle_commit.try_commit_pass2_bundle"]


def test_rejected_pass1_then_timeline_single_solver_summary_and_quarantine_zero() -> None:
    summary_msgs: list[str] = []

    def trace_cap(location: str, message: str, data: dict | None = None) -> None:
        if message == "solver_summary":
            summary_msgs.append(message)

    st = Pass12LayoutScratch(transport_cells={(10, 0)}, blocked_cells=set())
    cand = Pass12BundleCandidate(
        blocked_cells=frozenset({(8, 0)}),
        new_transport=frozenset({(2, 0)}),
        stub_cell=(2, 0),
    )
    is_ext = lambda c: c[0] >= 100  # noqa: E731
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace.trace_event",
        trace_cap,
    ):
        with trace_run_scope():
            assert not try_commit_pass1_bundle(st, cand, is_external=is_ext)
            out = build_solver_timeline({"BP": {"Entries": []}})
    assert summary_msgs.count("solver_summary") == 1
    assert out["solver_summary"]["quarantined_unrouted_count"] == 0


@override_settings(SHAPEZ_MINING_ASSERT_STEP9_ROUTING_STATE=True)
def test_build_solver_timeline_step9_routing_state_assert_passes() -> None:
    decoded: dict = {
        "BP": {
            "Entries": [{"X": x, "Y": 0, "T": "Layout_ShapeMiner"} for x in range(10, 13)]
            + [{"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0} for x in range(13, 30)]
        }
    }
    out = build_solver_timeline(decoded)
    assert out["return_reason"] == "ok"
    assert out["solver_termination"] == "success"


def test_build_solver_timeline_summary_p4_and_recovery_fields_consistent() -> None:
    """Phase A 회귀: P4·post_reclaim·recovery 필드의 존재·타입·상호 일관성 고정.

    `documents/ai/current_plan.md` 우선순위 1 (P4 이후 capacity·recovery·실데이터 회귀)을
    측정 가능한 단언으로 묶는다. P4가 실제로 도는 fixture에서 ``solver_summary``의
    P4 loop·post_reclaim_pass3·recovery_* 필드 계약을 깨뜨리지 않도록 한다.

    P4가 실행되면 loop 필드는 항상 채워지고, post_reclaim_pass3 필드는 permission·gate
    결과에 따라 ``pass3_summary``로만 일부 채워진다. 이 회귀는 채워진 필드의 타입과
    상호 일관성만 단언하고, optional 필드 부재는 통과시킨다.
    """

    decoded: dict = {
        "BP": {
            "Entries": [{"X": x, "Y": 0, "T": "Layout_ShapeMiner"} for x in range(10, 13)]
            + [{"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0} for x in range(13, 30)]
        }
    }
    out = build_solver_timeline(decoded)
    ss = out["solver_summary"]
    assert "pass3_reclaim_projected_net_internal_saved" in ss
    assert isinstance(ss["pass3_reclaim_projected_net_internal_saved"], int)

    p4_loop_fields = (
        "p4_reclaim_loop_max_iterations",
        "p4_reclaim_loop_iterations_executed",
        "p4_reclaim_loop_successful_commits",
        "p4_reclaim_loop_internal_transport_cumulative_added",
        "p4_reclaim_loop_terminated_reason",
    )
    if ss.get("p4_reclaim_loop_iterations_executed", 0):
        for key in p4_loop_fields:
            assert key in ss, f"missing P4 loop field: {key}"
        assert isinstance(ss["p4_reclaim_loop_iterations_executed"], int)
        assert isinstance(ss["p4_reclaim_loop_successful_commits"], int)
        assert isinstance(ss["p4_reclaim_loop_internal_transport_cumulative_added"], int)
        assert ss["p4_reclaim_loop_iterations_executed"] >= 1
        assert ss["p4_reclaim_loop_successful_commits"] >= 0
        assert isinstance(ss["p4_reclaim_loop_terminated_reason"], str)

    if "post_reclaim_pass3_executed" in ss:
        assert isinstance(ss["post_reclaim_pass3_executed"], bool)
        if ss["post_reclaim_pass3_executed"]:
            assert ss.get("post_reclaim_pass3_attempted") is True
            assert ss.get("post_reclaim_pass3_ran") is True
    if ss.get("post_reclaim_pass3_pass3_reverted"):
        assert ss.get("post_reclaim_pass3_executed") is True
    if "post_reclaim_pass3_reruns_used" in ss:
        assert isinstance(ss["post_reclaim_pass3_reruns_used"], int)
        assert ss["post_reclaim_pass3_reruns_used"] >= 0

    chain = ss.get("recovery_context_chain")
    if chain is not None:
        assert isinstance(chain, list)
        assert all(isinstance(seg, str) for seg in chain)
        for i in range(len(chain) - 1):
            assert chain[i] != chain[i + 1]

    trigger = ss.get("recovery_trigger_reason") or ss.get("recovery_trigger")
    p4_orch = ss.get("p4_orchestration_entry_segment")
    orchestration = p4_orch or trigger
    terminal = ss.get("recovery_terminal_reason")
    if orchestration is None:
        assert terminal is None
    else:
        assert isinstance(terminal, str) and terminal
        if ss.get("post_reclaim_pass3_map_accepted") is True:
            assert terminal == "post_reclaim_pass3_success"

    validate_frame = next(f for f in out["solver_timeline"] if f["id"] == "solver_validate")
    vs = validate_frame["summary"]
    assert vs.get("recovery_context_chain") == (chain if chain is not None else [])
    assert vs.get("recovery_trigger_reason") == trigger
    assert vs.get("p4_orchestration_entry_segment") == p4_orch
    assert vs.get("recovery_terminal_reason") == terminal
