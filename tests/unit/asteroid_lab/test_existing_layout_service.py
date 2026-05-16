"""A6 existing-layout service: ORM read, replay frames, persistence."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services import existing_layout_service as els


@pytest.fixture
def project_and_input() -> tuple[m.AsteroidProject, m.AsteroidMapInput]:
    proj = m.AsteroidProject.objects.create(name="A6", slug="a6-proj")
    decoded = {
        "V": 21,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 1, "Y": 1, "R": 0, "T": "Layout_FluidMiner"},
            ],
        },
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
    return m.ReplayTrack.objects.create(project=proj, track_key="a6-track")


@pytest.mark.django_db
def test_build_from_input_reads_decoded_json(
    project_and_input: tuple[m.AsteroidProject, m.AsteroidMapInput],
) -> None:
    _, inp = project_and_input
    ins = els.build_existing_layout_inspection_from_input(inp.id)
    assert ins.map_input_id == inp.id
    assert ins.project_id == inp.project_id
    assert len(ins.equipment) == 1


@pytest.mark.django_db
def test_record_existing_layout_inspection_frames_order_and_types(
    project_and_input: tuple[m.AsteroidProject, m.AsteroidMapInput],
    replay_track: m.ReplayTrack,
) -> None:
    _, inp = project_and_input
    ins = els.build_existing_layout_inspection_from_input(inp.id)
    frames = els.record_existing_layout_inspection_frames(replay_track.id, ins)
    assert len(frames) >= 4
    assert frames[0].event_type == et.EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_TRANSPORT
    assert frames[1].event_type == et.EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTRACTOR
    assert frames[2].event_type == et.EVENT_TYPE_REPLAY_SNAPSHOT_CLEANUP_EXTENSION
    recon_vals = {getattr(et, n) for n in dir(et) if n.startswith("EVENT_TYPE_RECONSTRUCTION_")}
    recon_frames = [f for f in frames[3:] if f.event_type in recon_vals]
    assert len(recon_frames) >= 1
    last = frames[-1]
    assert last.event_key == "step4_09_reconstruction_final"
    assert last.event_type == et.EVENT_TYPE_RECONSTRUCTION_MINEABLE_FINALIZED
    for i, fr in enumerate(frames):
        assert fr.frame_index == i

    rows = list(m.ReplayFrame.objects.filter(replay_track=replay_track).order_by("frame_index"))
    recon_row = rows[-1]
    assert recon_row.frame_payload.get("event_key") == "step4_09_reconstruction_final"
    assert recon_row.frame_payload.get("full_map") is not None
    assert isinstance(recon_row.cell_overlay_json.get("issue_cells"), list)
    summary = (recon_row.frame_payload or {}).get("summary") or {}
    assert "inspection_issue_count" in summary
    assert "visible_issue_cell_count" in summary
    issue_cells = recon_row.cell_overlay_json.get("issue_cells") or []
    assert summary["visible_issue_cell_count"] == len(issue_cells)

    for row in rows[:3]:
        etype = (row.frame_payload or {}).get("event_type")
        assert etype not in recon_vals
    assert any((r.frame_payload or {}).get("event_type") in recon_vals for r in rows[3:])


@pytest.mark.django_db
def test_persist_inspection_validates_project(
    project_and_input: tuple[m.AsteroidProject, m.AsteroidMapInput],
) -> None:
    proj, inp = project_and_input
    ins = els.build_existing_layout_inspection_from_input(inp.id)
    other = m.AsteroidProject.objects.create(name="X", slug="a6-other")
    with pytest.raises(ValueError, match="project_id"):
        els.persist_existing_layout_inspection_snapshot(other.id, inp.id, ins)

    pk = els.persist_existing_layout_inspection_snapshot(proj.id, inp.id, ins)
    row = m.AsteroidCellSnapshot.objects.get(pk=pk)
    assert row.layer == "existing_layout_inspection"
    assert row.cell_grid_json.get("inspection") is not None


@pytest.mark.django_db
def test_snapshot_from_input_does_not_mutate_decoded_json(
    project_and_input: tuple[m.AsteroidProject, m.AsteroidMapInput],
) -> None:
    _, inp = project_and_input
    before = dict(inp.decoded_json)
    els.build_existing_layout_inspection_from_input(inp.id)
    inp.refresh_from_db()
    assert inp.decoded_json == before
