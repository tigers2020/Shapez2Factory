"""PR-J: run_solver / runtime entry — macro_only_mode config → pipeline → DB milestones."""

from __future__ import annotations

import base64
import gzip
import json
from typing import Any

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
)
from django_apps.asteroid_lab.optimization.pipeline import PipelineResult
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
    _metrics_from_row,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import entry_result_to_json_dict
from tests.support.macro_triple_greenfield_fixture import build_macro_triple_greenfield_input
from tests.support.rttp_narrow_corridor_fixture import build_narrow_corridor_optimization_input
from tests.unit.asteroid_lab._runtime_game_data import run_solver_runtime_with_pinned_game_data

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module: object) -> object:
    return imported_game_data_batch_module


def _minimal_valid_copy() -> str:
    payload = json.dumps(
        {
            "V": 1,
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
                ],
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(payload)).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _frames_by_event_type(track_id: int) -> dict[str, m.ReplayFrame]:
    out: dict[str, m.ReplayFrame] = {}
    for row in m.ReplayFrame.objects.filter(replay_track_id=track_id).order_by("frame_index"):
        payload = dict(row.frame_payload or {})
        event_type = str(payload.get("event_type") or "")
        if event_type:
            out[event_type] = row
    return out


def _overlay_kinds(frame: m.ReplayFrame) -> set[str]:
    overlay = dict(frame.cell_overlay_json or {})
    cells = overlay.get("cells") or []
    return {str(c.get("kind")) for c in cells if isinstance(c, dict)}


def _milestone_by_type(
    milestones: list[dict[str, Any]],
    event_type: str,
) -> dict[str, Any]:
    for row in milestones:
        if row.get("event_type") == event_type:
            return row
    msg = f"missing milestone event_type={event_type!r}"
    raise AssertionError(msg)


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_runtime_passes_macro_only_pipeline_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Runtime entry must map config_json.macro_only_mode → RttpPipelineConfig."""

    import django_apps.asteroid_lab.services.solver_runtime_entry as entry_mod

    captured: list[RttpPipelineConfig] = []
    real_run = entry_mod.run_rttp_pipeline

    def _spy(*args: object, **kwargs: object) -> PipelineResult:
        cfg = kwargs.get("pipeline_config")
        assert isinstance(cfg, RttpPipelineConfig)
        captured.append(cfg)
        return real_run(*args, **kwargs)

    monkeypatch.setattr(entry_mod, "run_rttp_pipeline", _spy)

    macro_inp = build_macro_triple_greenfield_input()

    def _macro_optimization_input(
        _recon: object,
        *,
        cleanup: object = None,
        coord_frame: object = None,
        catalog_slice: object = None,
        complete_map: object = None,
    ) -> OptimizationInput:
        del _recon, cleanup, coord_frame, catalog_slice, complete_map
        return macro_inp

    monkeypatch.setattr(
        entry_mod,
        "optimization_input_from_reconstruction",
        _macro_optimization_input,
    )

    proj = m.AsteroidProject.objects.create(name="MacroSpy", slug="macro-j-spy")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    run_solver_runtime_with_pinned_game_data(
        int(proj.pk),
        run_key="macro-j-spy",
        config={
            "rttp_record_replay": True,
            SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY: True,
        },
    )

    assert captured
    assert captured[-1].macro_only_mode is True


@pytest.mark.skip(
    reason="Macro 4×4 fixture: no macro_normal/commits under OUTSIDE_MINEABLE (PR-B follow-up)"
)
@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_runtime_macro_only_db_and_milestone_readback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Full runtime path: macro_only_mode → DB :rttp frames + Section B milestones."""

    macro_inp = build_macro_triple_greenfield_input()

    def _macro_optimization_input(
        _recon: object,
        *,
        cleanup: object = None,
        coord_frame: object = None,
        catalog_slice: object = None,
        complete_map: object = None,
    ) -> OptimizationInput:
        del _recon, cleanup, coord_frame, catalog_slice, complete_map
        return macro_inp

    monkeypatch.setattr(
        "django_apps.asteroid_lab.services.solver_runtime_entry.optimization_input_from_reconstruction",
        _macro_optimization_input,
    )

    proj = m.AsteroidProject.objects.create(name="MacroRun", slug="macro-j-run")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    run_key = "macro-j-run"

    result = run_solver_runtime_with_pinned_game_data(
        int(proj.pk),
        run_key=run_key,
        config={
            "rttp_record_replay": True,
            SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY: True,
        },
    )

    assert result.ok is True
    assert result.validation_passed is True
    assert result.solver_run_id is not None

    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    assert run.config_json.get(SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY) is True

    track = m.ReplayTrack.objects.get(
        project_id=int(proj.pk),
        track_key=rttp_optimization_track_key(run_key),
    )
    assert m.ReplayFrame.objects.filter(replay_track_id=track.id).count() >= 4

    by_type = _frames_by_event_type(track.id)
    assert RTTP_MILESTONE_EVENT_TYPES <= set(by_type)

    candidate = by_type[et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT]
    cand_metrics = _metrics_from_row(candidate)
    assert cand_metrics.get("macro_normal_count", 0) >= 1
    assert cand_metrics.get("child_normal_count", 0) >= 3
    assert "macro.combined_footprint" in _overlay_kinds(candidate)

    commit = by_type[et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT]
    commit_metrics = _metrics_from_row(commit)
    assert commit_metrics.get("committed_macro_ids")
    assert commit_metrics.get("committed_child_ids")
    assert "macro.shared_lift" in _overlay_kinds(commit)

    selection = by_type[et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT]
    order = list(selection.metric_snapshot_json.get("commit_order") or [])
    assert order
    assert all(len(slot_id) == 64 for slot_id in order)

    body = entry_result_to_json_dict(result)
    milestones = body["lab_optimization_milestone_frames_json"]
    assert len(milestones) >= 4
    assert RTTP_MILESTONE_EVENT_TYPES <= {fr.get("event_type") for fr in milestones}

    commit_mile = _milestone_by_type(milestones, et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT)
    assert commit_mile["metrics"].get("committed_macro_ids")
    assert commit_mile["metrics"].get("committed_child_ids")

    cand_mile = _milestone_by_type(milestones, et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT)
    assert cand_mile["metrics"].get("macro_normal_count", 0) >= 1

    summary_order = result.solver_summary.get("commit_order") or []
    assert summary_order
    assert all(len(slot_id) == 64 for slot_id in summary_order)

    algo_steps = result.solver_summary.get("algorithm_steps") or []
    assert len(algo_steps) >= 5
    cand_step = next(
        row
        for row in algo_steps
        if row.get("event_type") == et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT
    )
    assert cand_step["metrics"].get("macro_normal_count", 0) >= 1
    commit_step = next(
        row
        for row in algo_steps
        if row.get("event_type") == et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT
    )
    assert commit_step["metrics"].get("committed_macro_ids")
    assert result.solver_summary.get("macro_only_mode") is True
    hud = result.solver_summary.get("macro_commit_summary")
    assert hud is not None
    assert hud["macro_only_mode"] is True
    assert hud["committed_macro_ids"]
    assert len(hud["committed_child_ids"]) == 3
    assert hud["domain_version"] is not None
    assert hud["validation_passed"] is True
    assert hud["conflict_count"] == 0
    run_summary = body.get("run_summary")
    assert run_summary is not None
    assert run_summary["macro_commit_summary"] == hud


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_runtime_default_config_stays_v01_non_macro(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default runtime config must not emit macro-only milestone metrics."""

    greenfield_inp = build_narrow_corridor_optimization_input()

    def _greenfield_optimization_input(
        _recon: object,
        *,
        cleanup: object = None,
        coord_frame: object = None,
        catalog_slice: object = None,
        complete_map: object = None,
    ) -> OptimizationInput:
        del _recon, cleanup, coord_frame, catalog_slice, complete_map
        return greenfield_inp

    monkeypatch.setattr(
        "django_apps.asteroid_lab.services.solver_runtime_entry.optimization_input_from_reconstruction",
        _greenfield_optimization_input,
    )

    proj = m.AsteroidProject.objects.create(name="MacroDefault", slug="macro-j-default")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    run_key = "macro-j-default"

    result = run_solver_runtime_with_pinned_game_data(
        int(proj.pk),
        run_key=run_key,
        config={"rttp_record_replay": True},
    )

    assert result.ok is True
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    assert not run.config_json.get(SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY)

    track = m.ReplayTrack.objects.get(
        project_id=int(proj.pk),
        track_key=rttp_optimization_track_key(run_key),
    )
    candidate = _frames_by_event_type(track.id)[et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT]
    cand_metrics = _metrics_from_row(candidate)
    assert "macro_normal_count" not in cand_metrics
    assert "child_normal_count" not in cand_metrics

    commit = _frames_by_event_type(track.id)[et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT]
    commit_metrics = _metrics_from_row(commit)
    assert "committed_macro_ids" not in commit_metrics

    body = entry_result_to_json_dict(result)
    milestones = body["lab_optimization_milestone_frames_json"]
    cand_mile = _milestone_by_type(milestones, et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT)
    assert "macro_normal_count" not in cand_mile["metrics"]

    order = result.solver_summary.get("commit_order") or []
    assert order
    assert all(len(slot_id) != 64 for slot_id in order)
    assert "macro_commit_summary" not in result.solver_summary
    run_summary = body.get("run_summary")
    assert run_summary is not None
    assert "macro_commit_summary" not in run_summary
