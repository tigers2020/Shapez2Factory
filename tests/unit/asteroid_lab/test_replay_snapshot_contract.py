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
    assert result.replay_frame_count == 5

    rows = list(
        m.ReplayFrame.objects.filter(replay_track_id=result.replay_track_id).order_by(
            "frame_index", "id"
        )
    )
    assert len(rows) == 5

    decode_row = rows[0]
    assert decode_row.frame_payload.get("event_type") == et.EVENT_TYPE_DECODE_NORMALIZED
    fm0 = decode_row.frame_payload.get("full_map")
    assert isinstance(fm0, list) and len(fm0) == 11
    kinds0 = {c["cell_kind"] for c in fm0}
    assert "fluid_miner" in kinds0
    assert "space_pipe" in kinds0
    assert "fluid_miner_extension" in kinds0
    assert "unknown" in kinds0
    diff0 = decode_row.frame_payload.get("diff") or {}
    assert diff0.get("removed") == []

    transport_row = rows[1]
    assert (
        transport_row.frame_payload.get("event_type")
        == et.EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT
    )
    fm1 = transport_row.frame_payload.get("full_map")
    assert isinstance(fm1, list) and len(fm1) == 10
    assert all(c["cell_kind"] != "space_pipe" for c in fm1)
    diff1 = transport_row.frame_payload.get("diff") or {}
    removed_kinds = {c["cell_kind"] for c in (diff1.get("removed") or [])}
    assert "space_pipe" in removed_kinds

    extractor_row = rows[2]
    fm2 = extractor_row.frame_payload.get("full_map")
    assert isinstance(fm2, list) and len(fm2) == 9
    assert all(c["cell_kind"] != "fluid_miner" for c in fm2)

    extension_row = rows[3]
    fm3 = extension_row.frame_payload.get("full_map")
    assert isinstance(fm3, list) and len(fm3) == 8
    assert all(c["cell_kind"] != "fluid_miner_extension" for c in fm3)

    recon_row = rows[4]
    assert recon_row.frame_payload.get("event_type") == et.EVENT_TYPE_REPLAY_SNAPSHOT_RECONSTRUCTION
    fm4 = recon_row.frame_payload.get("full_map")
    assert isinstance(fm4, list)
    voids = [c for c in fm4 if c.get("cell_kind") == "internal_void"]
    assert len(voids) >= 1
    diff4 = recon_row.frame_payload.get("diff") or {}
    added_kinds = {c.get("cell_kind") for c in (diff4.get("added") or [])}
    assert "internal_void" in added_kinds


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
