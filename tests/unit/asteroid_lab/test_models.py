"""ORM contracts for ``django_apps.asteroid_lab`` (UI replay, topology, hybrid solver artifacts)."""

from __future__ import annotations

from pathlib import Path

import pytest
from django.db import IntegrityError, transaction

import django_apps.asteroid_lab.models as al


@pytest.mark.django_db
def test_create_project_input_run_replay_frame() -> None:
    project = al.AsteroidProject.objects.create(name="Demo", slug="demo")
    inp = al.AsteroidMapInput.objects.create(
        project=project,
        source_kind=al.AsteroidMapInput.SourceKind.DECODED_JSON,
        decoded_json={"V": 1, "BP": {}},
    )
    run = al.SolverRun.objects.create(project=project, run_key="run-1", algorithm_label="ga_hybrid")
    track = al.ReplayTrack.objects.create(project=project, solver_run=run, track_key="main")
    frame = al.ReplayFrame.objects.create(
        replay_track=track,
        frame_index=0,
        frame_key="init",
        phase="bootstrap",
        title="Start",
    )
    assert frame.replay_track.project_id == project.id
    assert inp.project_id == project.id
    assert run.project_id == project.id


@pytest.mark.django_db
def test_playback_session_updates_current_frame() -> None:
    project = al.AsteroidProject.objects.create(name="P", slug="p-playback")
    track = al.ReplayTrack.objects.create(project=project, track_key="t1")
    session = al.UIPlaybackSession.objects.create(replay_track=track)
    assert session.current_frame_index == 0
    session.current_frame_index = 3
    session.is_playing = True
    session.playback_speed_ms = 400
    session.selected_layer = "layer_a"
    session.save()
    session.refresh_from_db()
    assert session.current_frame_index == 3
    assert session.is_playing is True
    assert session.playback_speed_ms == 400
    assert session.selected_layer == "layer_a"


@pytest.mark.django_db
def test_topology_rule_modal_content_loads() -> None:
    rule = al.TopologyRule.objects.create(
        rule_key="stub_must_face_trunk",
        title="Stub orientation",
        short_label="Stub",
        rule_group="routing",
        description="Summary line",
    )
    modal = al.TopologyRuleModalContent.objects.create(
        rule=rule,
        modal_title="Stub orientation (details)",
        lead_html="<p>Detail body</p>",
        sections_json=[{"heading": "Example", "body": "…"}],
    )
    loaded = al.TopologyRuleModalContent.objects.select_related("rule").get(pk=modal.pk)
    assert loaded.rule.rule_key == "stub_must_face_trunk"
    assert loaded.modal_title
    assert loaded.sections_json


@pytest.mark.django_db
def test_candidate_bundle_gene_fields() -> None:
    project = al.AsteroidProject.objects.create(name="G", slug="g-bundle")
    run = al.SolverRun.objects.create(project=project, run_key="r1")
    bundle = al.CandidateBundle.objects.create(
        solver_run=run,
        bundle_key="gene-aa",
        generation_index=2,
        extractor_coord={"x": 1, "y": 2},
        output_direction="north",
        output_stub_coord={"x": 1, "y": 1},
        extension_pattern_key="L2",
        extension_coords_json=[{"x": 2, "y": 2}],
        transport_kind="belt",
        local_score=0.42,
        fitness_json={"throughput": 10.0},
    )
    bundle.refresh_from_db()
    assert bundle.extractor_coord == {"x": 1, "y": 2}
    assert bundle.output_direction == "north"
    assert bundle.extension_pattern_key == "L2"
    assert bundle.extension_coords_json == [{"x": 2, "y": 2}]


@pytest.mark.django_db
def test_routing_probe_reachable_and_unreachable() -> None:
    project = al.AsteroidProject.objects.create(name="R", slug="r-probe")
    run = al.SolverRun.objects.create(project=project, run_key="r1")
    bundle = al.CandidateBundle.objects.create(
        solver_run=run,
        bundle_key="b1",
        extractor_coord={"x": 0, "y": 0},
        output_direction="east",
        output_stub_coord={"x": 1, "y": 0},
        transport_kind="belt",
    )
    ok = al.RoutingProbe.objects.create(
        candidate_bundle=bundle,
        start_stub_coord={"x": 1, "y": 0},
        reachable=True,
        path_cost=1.5,
        path_cells_json=[{"x": 1, "y": 0}, {"x": 2, "y": 0}],
        explored_count=4,
    )
    bad = al.RoutingProbe.objects.create(
        candidate_bundle=bundle,
        start_stub_coord={"x": 9, "y": 9},
        reachable=False,
        failure_reason="blocked",
        explored_count=99,
    )
    assert ok.reachable is True
    assert bad.reachable is False
    assert bad.failure_reason == "blocked"


@pytest.mark.django_db
def test_solver_metric_snapshot_fitness_components() -> None:
    project = al.AsteroidProject.objects.create(name="M", slug="m-metric")
    run = al.SolverRun.objects.create(project=project, run_key="r1")
    snap = al.SolverMetricSnapshot.objects.create(
        solver_run=run,
        frame_index=5,
        phase="ga_generation",
        fitness_components_json={"layout": 0.8, "routing": 0.2},
        aggregate_score=0.73,
        throughput_hint=12.5,
    )
    snap.refresh_from_db()
    assert snap.fitness_components_json["layout"] == 0.8
    assert snap.aggregate_score == pytest.approx(0.73)


@pytest.mark.django_db
def test_ui_playback_session_one_to_one_replay_track() -> None:
    """Phase 1: ``UIPlaybackSession.replay_track`` is ``OneToOneField`` (one session per track)."""

    project = al.AsteroidProject.objects.create(name="O", slug="o-121")
    track = al.ReplayTrack.objects.create(project=project, track_key="t")
    al.UIPlaybackSession.objects.create(replay_track=track, current_frame_index=1)
    assert al.UIPlaybackSession.objects.filter(replay_track=track).count() == 1
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            al.UIPlaybackSession.objects.create(replay_track=track, current_frame_index=2)


@pytest.mark.django_db
def test_replay_frames_default_order_by_frame_index() -> None:
    project = al.AsteroidProject.objects.create(name="O", slug="o-order")
    track = al.ReplayTrack.objects.create(project=project, track_key="ord")
    al.ReplayFrame.objects.create(
        replay_track=track,
        frame_index=2,
        frame_key="c",
        phase="p",
        title="t3",
    )
    al.ReplayFrame.objects.create(
        replay_track=track,
        frame_index=0,
        frame_key="a",
        phase="p",
        title="t1",
    )
    al.ReplayFrame.objects.create(
        replay_track=track,
        frame_index=1,
        frame_key="b",
        phase="p",
        title="t2",
    )
    ordered = list(track.frames.values_list("frame_index", flat=True))
    assert ordered == [0, 1, 2]


def test_asteroid_lab_models_module_has_no_shapez_asteroid_solver_imports() -> None:
    """Persistence layer must not depend on v1/v2 asteroid solver packages."""

    text = Path(al.__file__).read_text(encoding="utf-8")
    assert "django_apps.shapez_asteroid" not in text
    assert "asteroid_mining_layout_v2" not in text
    assert "asteroid_mining_layout_v1" not in text
