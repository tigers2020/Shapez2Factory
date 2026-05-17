"""Replay contract: every frame carries a full_map snapshot + optional diff (UI-only)."""

from __future__ import annotations

import base64
import gzip
import json

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services import project_service
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)
from django_apps.web.services.asteroid_lab_page_context import serialize_replay_frame


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


@pytest.mark.django_db
def test_replay_frames_are_full_map_snapshots_not_event_only() -> None:
    def corner(x: int, y: int) -> dict:
        return {"X": x, "Y": y, "R": 0, "T": "UnknownTile_Xy"}

    root = {
        "V": 3,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "Layout_FluidMiner"},
                {"X": 2, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 3, "Y": 0, "R": 0, "T": "Layout_FluidMinerExtension"},
                corner(1, 1),
                corner(2, 1),
                corner(3, 1),
                corner(1, 2),
                corner(3, 2),
                corner(1, 3),
                corner(2, 3),
                corner(3, 3),
            ],
        },
    }
    code = _encode_v4_copy(root)
    dto = project_service.create_project_from_copy_code(code, source_label="snap-contract")
    result = build_initial_replay_for_map_input(dto.map_input_id)
    assert result.status == "ok"
    assert result.replay_frame_count >= 6

    rows = list(
        m.ReplayFrame.objects.filter(replay_track_id=result.replay_track_id).order_by(
            "frame_index", "id"
        )
    )
    assert len(rows) >= 6

    raw_row = rows[0]
    assert raw_row.frame_payload.get("event_type") == et.EVENT_TYPE_DECODE_RAW_LOADED
    assert raw_row.frame_payload.get("event_key") == "step0_decode_raw"
    fm_raw = raw_row.frame_payload.get("full_map")
    assert isinstance(fm_raw, list) and len(fm_raw) == 11
    kinds_raw = {c["cell_kind"] for c in fm_raw}
    assert "space_pipe" in kinds_raw
    assert "fluid_miner" in kinds_raw
    diff_raw = raw_row.frame_payload.get("diff") or {}
    assert diff_raw == {"added": [], "removed": [], "changed": []}

    decode_row = rows[1]
    assert decode_row.frame_payload.get("event_type") == et.EVENT_TYPE_DECODE_NORMALIZED
    fm0 = decode_row.frame_payload.get("full_map")
    assert isinstance(fm0, list) and len(fm0) == 10
    kinds0 = {c["cell_kind"] for c in fm0}
    assert "fluid_miner" in kinds0
    assert "space_pipe" not in kinds0
    assert "fluid_miner_extension" in kinds0
    assert "unknown" in kinds0
    diff0 = decode_row.frame_payload.get("diff") or {}
    removed0 = diff0.get("removed") or []
    assert any(c.get("cell_kind") == "space_pipe" for c in removed0)

    transport_row = rows[2]
    assert (
        transport_row.frame_payload.get("event_type")
        == et.EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT
    )
    fm1 = transport_row.frame_payload.get("full_map")
    assert isinstance(fm1, list) and len(fm1) == 10
    assert fm1 == fm0
    assert all(c["cell_kind"] != "space_pipe" for c in fm1)
    diff1 = transport_row.frame_payload.get("diff") or {}
    assert diff1 == {"added": [], "removed": [], "changed": []}

    extractor_row = rows[3]
    fm2 = extractor_row.frame_payload.get("full_map")
    assert isinstance(fm2, list) and len(fm2) == 10
    assert all(c["cell_kind"] != "fluid_miner" for c in fm2)
    cell_10 = next(c for c in fm2 if c["x"] == 1 and c["y"] == 0)
    assert cell_10["cell_kind"] == "asteroid_fluid_field"
    diff2 = extractor_row.frame_payload.get("diff") or {}
    changed2 = diff2.get("changed") or []
    assert any(
        ch.get("before", {}).get("cell_kind") == "fluid_miner"
        and ch.get("after", {}).get("cell_kind") == "asteroid_fluid_field"
        for ch in changed2
    )

    extension_row = rows[4]
    fm3 = extension_row.frame_payload.get("full_map")
    assert isinstance(fm3, list) and len(fm3) == 10
    assert all(c["cell_kind"] != "fluid_miner_extension" for c in fm3)
    cell_30 = next(c for c in fm3 if c["x"] == 3 and c["y"] == 0)
    assert cell_30["cell_kind"] == "asteroid_fluid_field"
    diff3 = extension_row.frame_payload.get("diff") or {}
    changed3 = diff3.get("changed") or []
    assert any(
        ch.get("before", {}).get("cell_kind") == "fluid_miner_extension"
        and ch.get("after", {}).get("cell_kind") == "asteroid_fluid_field"
        for ch in changed3
    )

    payloads = [r.frame_payload or {} for r in rows]
    final_payload = next(
        p for p in payloads if p.get("event_key") == "step4_09_reconstruction_final"
    )
    complete_payload = rows[-1].frame_payload or {}
    assert complete_payload.get("event_key") == "step4_10_asteroid_map_complete"
    assert complete_payload.get("event_type") == et.EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE
    assert complete_payload.get("full_map") == final_payload.get("full_map")
    assert complete_payload.get("diff") == final_payload.get("diff")
    assert complete_payload.get("is_decision_point") is False

    assert final_payload.get("event_type") == et.EVENT_TYPE_RECONSTRUCTION_MINEABLE_FINALIZED
    fm4 = final_payload.get("full_map")
    assert isinstance(fm4, list)
    assert all(c.get("cell_kind") != "internal_void" for c in fm4)
    hole = next(c for c in fm4 if c.get("x") == 2 and c.get("y") == 2)
    assert hole.get("cell_kind") == "asteroid_shape_field"
    diff4 = final_payload.get("diff") or {}
    added_kinds = {c.get("cell_kind") for c in (diff4.get("added") or [])}
    if added_kinds:
        assert "asteroid_shape_field" in added_kinds
    rs = final_payload.get("summary") or {}
    assert int(rs.get("barrier_cell_count", 0)) >= int(rs.get("wall_cell_count", 0))
    assert "inferred_shell_cell_count" in rs
    assert "external_reachable_count" in rs
    assert int(rs.get("filled_hole_cell_count", -1)) >= 1
    assert complete_payload.get("summary") == rs


@pytest.mark.django_db
def test_serialize_replay_frame_lifts_full_map_and_frame_id() -> None:
    p = m.AsteroidProject.objects.create(name="Ser", slug="ser-lab")
    t = m.ReplayTrack.objects.create(project=p, track_key="ser-tr")
    row = m.ReplayFrame.objects.create(
        replay_track=t,
        frame_index=0,
        frame_key="step0_decode",
        phase="decode",
        title="Decoded blueprint",
        description="",
        frame_payload={
            "event_type": et.EVENT_TYPE_DECODE_NORMALIZED,
            "full_map": [{"x": 1, "y": 0, "cell_kind": "shape_belt", "layer": None}],
            "diff": {"added": [], "removed": [], "changed": []},
            "summary": {"belt_count": 1, "pipe_count": 0},
        },
        cell_overlay_json={},
        metric_snapshot_json={},
    )
    ser = serialize_replay_frame(row)
    assert ser["frame_id"] == "step0_decode"
    assert ser["full_map"][0]["cell_kind"] == "shape_belt"
    assert ser["diff"]["removed"] == []
    assert ser["summary"]["belt_count"] == 1
