"""A5 cell snapshot service: ORM read, replay frames, persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services import cell_snapshot_service as css
from django_apps.asteroid_lab.services import existing_layout_service as els
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)


@pytest.fixture
def project_and_input() -> tuple[m.AsteroidProject, m.AsteroidMapInput]:
    proj = m.AsteroidProject.objects.create(name="S5", slug="s5-proj")
    decoded = {
        "V": 11,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 2, "Y": 0, "R": 0, "T": "SpaceBelt_Left"},
            ],
        },
        "_asteroid_lab_summary": {"entry_count": 2},
    }
    inp = m.AsteroidMapInput.objects.create(
        project=proj,
        source_kind=m.AsteroidMapInput.SourceKind.DECODED_JSON,
        decoded_json=decoded,
    )
    return proj, inp


@pytest.fixture
def replay_track(project_and_input: tuple[m.AsteroidProject, m.AsteroidMapInput]) -> m.ReplayTrack:
    proj, _ = project_and_input
    return m.ReplayTrack.objects.create(project=proj, track_key="s5-track")


@pytest.mark.django_db
def test_build_decoded_blueprint_snapshot_from_input_reads_decoded_json(
    project_and_input: tuple[m.AsteroidProject, m.AsteroidMapInput],
) -> None:
    _, inp = project_and_input
    snap = css.build_decoded_blueprint_snapshot_from_input(inp.id)
    assert snap.map_input_id == inp.id
    assert snap.project_id == inp.project_id
    assert snap.binary_version == 11
    assert snap.entry_count == 2
    assert len(snap.cells) == 2


@pytest.mark.django_db
def test_record_decoded_snapshot_frames_single_full_map_decode(
    project_and_input: tuple[m.AsteroidProject, m.AsteroidMapInput],
    replay_track: m.ReplayTrack,
) -> None:
    _, inp = project_and_input
    snap = css.build_decoded_blueprint_snapshot_from_input(inp.id)
    frames = css.record_decoded_snapshot_frames(replay_track.id, snap)
    assert len(frames) == 2
    assert frames[0].frame_index == 0
    assert frames[1].frame_index == 1

    rows = list(m.ReplayFrame.objects.filter(replay_track=replay_track).order_by("frame_index"))
    assert len(rows) == 2
    raw_row, norm_row = rows[0], rows[1]
    assert raw_row.frame_key == "step0_decode_raw"
    assert raw_row.title == "Decoded blueprint (raw)"
    assert raw_row.frame_payload["event_type"] == et.EVENT_TYPE_DECODE_RAW_LOADED
    assert raw_row.frame_payload["event_key"] == "step0_decode_raw"
    fm_raw = raw_row.frame_payload.get("full_map")
    assert isinstance(fm_raw, list) and len(fm_raw) == 2
    kinds_raw = {c["cell_kind"] for c in fm_raw}
    assert "space_pipe" in kinds_raw
    assert "space_belt" in kinds_raw
    diff_raw = raw_row.frame_payload.get("diff") or {}
    assert diff_raw == {"added": [], "removed": [], "changed": []}
    cells_raw = raw_row.cell_overlay_json.get("cells")
    assert isinstance(cells_raw, list) and len(cells_raw) == 2
    assert raw_row.metric_snapshot_json.get("cell_kind_counts") == {
        "space_pipe": 1,
        "space_belt": 1,
    }

    assert norm_row.frame_key == "step0_decode"
    assert norm_row.title == "Decoded blueprint"
    assert norm_row.frame_payload["event_type"] == et.EVENT_TYPE_DECODE_NORMALIZED
    assert norm_row.frame_payload["event_key"] == "step0_decode"
    fm = norm_row.frame_payload.get("full_map")
    assert isinstance(fm, list) and len(fm) == 0
    kinds = {c["cell_kind"] for c in fm}
    assert "space_pipe" not in kinds
    assert "space_belt" not in kinds
    diff = norm_row.frame_payload.get("diff") or {}
    removed = diff.get("removed") or []
    assert any(c.get("cell_kind") == "space_pipe" for c in removed)
    assert any(c.get("cell_kind") == "space_belt" for c in removed)
    assert diff.get("added") == []
    assert diff.get("changed") == []
    cells = norm_row.cell_overlay_json.get("cells")
    assert isinstance(cells, list) and len(cells) == 0
    assert norm_row.metric_snapshot_json.get("cell_kind_counts") == {}


@pytest.mark.django_db
def test_record_step0_decode_matches_step1_transport_full_map_empty_transport_diff(
    project_and_input: tuple[m.AsteroidProject, m.AsteroidMapInput],
    replay_track: m.ReplayTrack,
) -> None:
    _, inp = project_and_input
    snap = css.build_decoded_blueprint_snapshot_from_input(inp.id)
    ins = els.build_existing_layout_inspection_from_input(inp.id)
    css.record_decoded_snapshot_frames(replay_track.id, snap)
    els.record_existing_layout_inspection_frames(replay_track.id, ins)

    rows = list(m.ReplayFrame.objects.filter(replay_track=replay_track).order_by("frame_index"))
    assert len(rows) >= 6
    p0 = rows[0].frame_payload or {}
    p1 = rows[1].frame_payload or {}
    p2 = rows[2].frame_payload or {}
    assert p0.get("event_key") == "step0_decode_raw"
    assert p1.get("event_key") == "step0_decode"
    assert p2.get("event_key") == "step1_cleanup_transport"
    assert p1.get("full_map") == p2.get("full_map")
    assert p2.get("diff") == {"added": [], "removed": [], "changed": []}


@pytest.mark.django_db
def test_no_reconstruction_event_types_emitted(
    project_and_input: tuple[m.AsteroidProject, m.AsteroidMapInput],
    replay_track: m.ReplayTrack,
) -> None:
    _, inp = project_and_input
    snap = css.build_decoded_blueprint_snapshot_from_input(inp.id)
    css.record_decoded_snapshot_frames(replay_track.id, snap)
    allowed = {et.EVENT_TYPE_DECODE_RAW_LOADED, et.EVENT_TYPE_DECODE_NORMALIZED}
    for row in m.ReplayFrame.objects.filter(replay_track=replay_track).order_by("frame_index"):
        etype = (row.frame_payload or {}).get("event_type")
        assert etype in allowed


@pytest.mark.django_db
def test_persist_decoded_cell_snapshot_creates_row(
    project_and_input: tuple[m.AsteroidProject, m.AsteroidMapInput],
) -> None:
    proj, inp = project_and_input
    snap = css.build_decoded_blueprint_snapshot_from_input(inp.id)
    pk = css.persist_decoded_cell_snapshot(proj.id, inp.id, snap)
    row = m.AsteroidCellSnapshot.objects.get(pk=pk)
    assert row.layer == "decoded_blueprint_top"
    assert len(row.overlay_json["cells"]) == 2


@pytest.mark.django_db
def test_persist_wrong_project_raises(
    project_and_input: tuple[m.AsteroidProject, m.AsteroidMapInput],
) -> None:
    proj, inp = project_and_input
    other = m.AsteroidProject.objects.create(name="O", slug="o-other")
    snap = css.build_decoded_blueprint_snapshot_from_input(inp.id)
    with pytest.raises(ValueError, match="project_id"):
        css.persist_decoded_cell_snapshot(other.id, inp.id, snap)


def test_cell_snapshot_service_avoids_mining_solver_paths() -> None:
    root = Path(__file__).resolve().parents[3]
    path = root / "django_apps" / "asteroid_lab" / "services" / "cell_snapshot_service.py"
    text = path.read_text(encoding="utf-8")
    forbidden = (
        "django_apps.shapez_asteroid",
        "django_apps.shapez_solver",
        "asteroid_mining_layout_v2",
    )
    for bad in forbidden:
        assert bad not in text


def test_snapshots_package_avoids_mining_solver_paths() -> None:
    root = Path(__file__).resolve().parents[3]
    for rel in ("snapshots/decoded_blueprint_snapshot.py", "snapshots/cell_classifier.py"):
        text = (root / "django_apps" / "asteroid_lab" / rel).read_text(encoding="utf-8")
        for bad in ("shapez_asteroid", "shapez_solver", "asteroid_mining_layout"):
            assert bad not in text


@pytest.mark.django_db
def test_build_from_input_empty_bp_entries() -> None:
    proj = m.AsteroidProject.objects.create(name="E", slug="e-empty")
    inp = m.AsteroidMapInput.objects.create(
        project=proj,
        source_kind=m.AsteroidMapInput.SourceKind.DECODED_JSON,
        decoded_json={"V": 0, "BP": {"$type": "Island", "Entries": []}},
    )
    snap = css.build_decoded_blueprint_snapshot_from_input(inp.id)
    assert snap.cells == ()
    assert snap.entry_count == 0


def test_manual_snapshot_replay_not_used_as_algorithm_input_doc() -> None:
    """Replay rows are write-only in this service path (contract reminder for readers)."""

    snap = DecodedBlueprintSnapshotDTO(
        project_id=None,
        map_input_id=None,
        binary_version=1,
        blueprint_type="Island",
        entry_count=1,
        bbox_json={"min_x": 1, "max_x": 1, "min_y": 0, "max_y": 0, "width": 1, "height": 1},
        cell_kind_counts_json={"space_pipe": 1},
        transport_kind_counts_json={"fluid_pipe": 1},
        cells=(
            DecodedCellDTO(
                x=1,
                y=0,
                layer=None,
                rotation=0,
                tile_type="SpacePipe_X",
                cell_kind="space_pipe",
                transport_kind="fluid_pipe",
                has_nested_blueprint=False,
                nested_entry_count=0,
                nested_type_counts_json={},
                raw_entry_json={"X": 1, "Y": 0, "T": "SpacePipe_X"},
            ),
        ),
        summary_json={},
    )
    built = build_decoded_blueprint_snapshot(
        {
            "V": 1,
            "BP": {"$type": "Island", "Entries": [{"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_X"}]},
        }
    )
    assert built.cell_kind_counts_json == snap.cell_kind_counts_json
