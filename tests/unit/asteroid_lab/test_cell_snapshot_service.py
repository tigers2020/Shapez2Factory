"""A5 cell snapshot service: ORM read, replay frames, persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services import cell_snapshot_service as css
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
def test_record_decoded_snapshot_frames_raw_and_normalized(
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
    assert rows[0].title == "Raw copy decoded"
    assert rows[0].frame_payload["event_type"] == et.EVENT_TYPE_DECODE_RAW_LOADED
    assert rows[1].title == "Decoded blueprint normalized"
    assert rows[1].frame_payload["event_type"] == et.EVENT_TYPE_DECODE_NORMALIZED
    cells = rows[1].cell_overlay_json.get("cells")
    assert isinstance(cells, list) and len(cells) == 2
    assert {c["cell_kind"] for c in cells} == {"space_pipe", "space_belt"}
    assert rows[1].metric_snapshot_json.get("cell_kind_counts") == snap.cell_kind_counts_json


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
