"""Timeline wire must carry equipment_bundles for Lab map highlight."""

from __future__ import annotations

import base64
import gzip
import json

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.replay.lab_timeline_adapter import lab_replay_row_to_timeline_frame
from django_apps.asteroid_lab.services import project_service
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    _frame_row_from_model,
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    return "SHAPEZ2-4-" + base64.b64encode(gzip.compress(text)).decode("ascii")


@pytest.mark.django_db
def test_pipeline_persisted_cleanup_transport_has_equipment_bundles() -> None:
    root = {
        "V": 88,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }
    dto = project_service.create_project_from_copy_code(
        _encode_v4_copy(root), source_label="bundle-wire"
    )
    build_initial_replay_for_map_input(dto.map_input_id)
    row = (
        m.ReplayFrame.objects.filter(
            replay_track__project_id=dto.project_id,
            frame_payload__event_type=et.EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT,
        )
        .order_by("frame_index", "id")
        .first()
    )
    assert row is not None
    co = row.cell_overlay_json or {}
    fm = (row.frame_payload or {}).get("full_map") or []
    kinds = {c.get("cell_kind") for c in fm if isinstance(c, dict)}
    eb = co.get("equipment_bundles")
    assert isinstance(eb, list), f"ORM overlay keys={list(co.keys())}"
    timeline_frame = lab_replay_row_to_timeline_frame(_frame_row_from_model(row))
    wire_eb = timeline_frame.cell_overlay_json.get("equipment_bundles")
    assert wire_eb, f"timeline frame missing bundles; full_map kinds={kinds}"
    frames, _ = build_lab_replay_frames_for_project(int(dto.project_id))
    assert any(
        isinstance(f.get("cell_overlay_json"), dict)
        and f["cell_overlay_json"].get("equipment_bundles")
        for f in frames
    )
