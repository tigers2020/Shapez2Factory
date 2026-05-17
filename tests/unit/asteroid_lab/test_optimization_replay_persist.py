"""12C/12D — Persist optimization replay frames on ``SolverRun`` (output-only)."""

from __future__ import annotations

import base64
import gzip
import json
from dataclasses import replace

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services import project_service
from django_apps.asteroid_lab.services.optimization_replay_persist import (
    attach_optimization_replay_frames_after_successful_replay_build,
    persist_optimization_replay_frames_to_solver_run,
)
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)
from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import OptimizationReplayFrame
from django_apps.shapez_asteroid.optimization.enums import OptimizationReplayEventType
from django_apps.shapez_asteroid.optimization.optimization_ui_payload import (
    OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY,
    SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY,
    empty_optimization_replay_track_payload_with_diagnostic,
)
from django_apps.web.services import asteroid_lab_page_context as alc
from django_apps.web.services.asteroid_lab_post_inspection_evolution import (
    run_post_inspection_evolution_and_attach_optimization_replay,
)


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _minimal_root(*, version: int = 42) -> dict:
    return {
        "V": version,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }


def _one_valid_frame() -> tuple[OptimizationReplayFrame, ...]:
    return (
        OptimizationReplayFrame(
            frame_index=0,
            event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
            title="t",
            description="d",
            visible_cells=(Coord(1, 0),),
            overlay_cells=(),
            metrics={"k": 1},
        ),
    )


pytestmark = [pytest.mark.slow, pytest.mark.django_db]


def test_persist_preserves_unrelated_config_json_keys() -> None:
    code = _encode_v4_copy(_minimal_root(version=501))
    dto = project_service.create_project_from_copy_code(code, source_label="persist-keys")
    result = build_initial_replay_for_map_input(
        dto.map_input_id, config={"solver_meta": {"seed": 7}}
    )
    assert result.status == "ok"
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    assert run.config_json.get("solver_meta") == {"seed": 7}
    persist_optimization_replay_frames_to_solver_run(run, _one_valid_frame())
    run.refresh_from_db()
    assert run.config_json.get("solver_meta") == {"seed": 7}
    assert SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY in run.config_json


def test_persist_writes_optimization_replay_frames_list() -> None:
    code = _encode_v4_copy(_minimal_root(version=502))
    dto = project_service.create_project_from_copy_code(code, source_label="persist-list")
    result = build_initial_replay_for_map_input(dto.map_input_id)
    assert result.status == "ok"
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    persist_optimization_replay_frames_to_solver_run(run, _one_valid_frame())
    run.refresh_from_db()
    raw = run.config_json[SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY]
    assert isinstance(raw, list) and len(raw) == 1
    assert raw[0]["title"] == "t"
    assert raw[0]["frame_index"] == 0


def test_persist_empty_frames_does_not_mutate_solver_run_config_json() -> None:
    code = _encode_v4_copy(_minimal_root(version=503))
    dto = project_service.create_project_from_copy_code(code, source_label="noop")
    result = build_initial_replay_for_map_input(dto.map_input_id)
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    before = dict(run.config_json or {})
    persist_optimization_replay_frames_to_solver_run(run, ())
    run.refresh_from_db()
    assert run.config_json == before


def test_attach_then_lab_page_context_reports_nonzero_frames() -> None:
    code = _encode_v4_copy(_minimal_root(version=504))
    dto = project_service.create_project_from_copy_code(code, source_label="attach-ctx")
    result = build_initial_replay_for_map_input(dto.map_input_id)
    assert result.status == "ok"
    out = attach_optimization_replay_frames_after_successful_replay_build(
        result, _one_valid_frame()
    )
    assert out.attached is True and out.reason == "attached"
    ctx = alc.lab_page_context(project_id=dto.project_id)
    opt = ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]
    assert opt["frame_count"] == 1
    assert opt["frames"][0]["title"] == "t"


def test_attach_empty_frames_preserves_existing_optimization_replay() -> None:
    code = _encode_v4_copy(_minimal_root(version=507))
    dto = project_service.create_project_from_copy_code(code, source_label="empty-attach")
    result = build_initial_replay_for_map_input(dto.map_input_id)
    assert result.status == "ok"
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    persist_optimization_replay_frames_to_solver_run(run, _one_valid_frame())
    run.refresh_from_db()
    before_len = len(run.config_json[SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY])
    out = attach_optimization_replay_frames_after_successful_replay_build(result, ())
    assert out.attached is False and out.reason == "empty_frames"
    run.refresh_from_db()
    after = run.config_json[SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY]
    assert isinstance(after, list) and len(after) == before_len


def test_get_latest_skips_invalid_persisted_blob_on_newest_run() -> None:
    code = _encode_v4_copy(_minimal_root(version=505))
    dto = project_service.create_project_from_copy_code(code, source_label="invalid-blob")
    r1 = build_initial_replay_for_map_input(dto.map_input_id)
    run_bad = m.SolverRun.objects.get(pk=int(r1.solver_run_id))
    merged = dict(run_bad.config_json or {})
    merged[SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY] = [{"not": "a frame"}]
    run_bad.config_json = merged
    run_bad.save(update_fields=["config_json"])

    r2 = build_initial_replay_for_map_input(dto.map_input_id, force=True)
    assert r2.status == "ok"
    run_new = m.SolverRun.objects.get(pk=int(r2.solver_run_id))
    persist_optimization_replay_frames_to_solver_run(run_new, _one_valid_frame())

    ctx = alc.lab_page_context(project_id=dto.project_id)
    assert ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]["frame_count"] == 1


def test_attach_does_not_mutate_inspection_config_passed_at_create() -> None:
    """Replay blob is merged post-create; caller ``config`` is unchanged on disk except merge."""

    code = _encode_v4_copy(_minimal_root(version=506))
    dto = project_service.create_project_from_copy_code(code, source_label="config-split")
    result = build_initial_replay_for_map_input(dto.map_input_id, config={"only_algo": True})
    out = attach_optimization_replay_frames_after_successful_replay_build(
        result, _one_valid_frame()
    )
    assert out.attached is True
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    assert run.config_json.get("only_algo") is True
    assert isinstance(run.config_json.get(SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY), list)


def test_attach_noop_on_failed_pipeline() -> None:
    dto = project_service.create_project_from_copy_code(
        "not-a-valid-shapez-copy", source_label="bad"
    )
    result = build_initial_replay_for_map_input(dto.map_input_id)
    assert result.status == "failed"
    out = attach_optimization_replay_frames_after_successful_replay_build(
        result, _one_valid_frame()
    )
    assert out.attached is False and out.reason == "non_ok_result"
    assert m.SolverRun.objects.filter(project_id=dto.project_id).count() == 0


def test_run_post_inspection_evolution_attaches_replay_frames() -> None:
    code = _encode_v4_copy(_minimal_root(version=509))
    dto = project_service.create_project_from_copy_code(code, source_label="wire-12d")
    result = build_initial_replay_for_map_input(dto.map_input_id)
    assert result.status == "ok"
    wire = run_post_inspection_evolution_and_attach_optimization_replay(dto.map_input_id, result)
    assert wire.attached is True and wire.reason == "attached"
    ctx = alc.lab_page_context(project_id=dto.project_id)
    assert ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY]["frame_count"] > 0


def test_run_post_inspection_empty_candidate_pool_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    from django_apps.shapez_asteroid.optimization.dto import CandidateGenerationResult

    code = _encode_v4_copy(_minimal_root(version=601))
    dto = project_service.create_project_from_copy_code(code, source_label="empty-pool")
    result = build_initial_replay_for_map_input(dto.map_input_id)
    assert result.status == "ok"

    def fake_generate(
        *args: object,
        replay_recorder: object | None = None,
        **kwargs: object,
    ) -> CandidateGenerationResult:
        return CandidateGenerationResult(normal_candidates=(), rejected_candidates=())

    monkeypatch.setattr(
        "django_apps.web.services.asteroid_lab_post_inspection_evolution.generate_bundle_candidates",
        fake_generate,
    )
    wire = run_post_inspection_evolution_and_attach_optimization_replay(dto.map_input_id, result)
    assert wire.attached is False and wire.reason == "empty_candidate_pool"


def test_attach_solver_run_not_found_returns_reason() -> None:
    code = _encode_v4_copy(_minimal_root(version=508))
    dto = project_service.create_project_from_copy_code(code, source_label="missing-run")
    result = build_initial_replay_for_map_input(dto.map_input_id)
    assert result.status == "ok"
    bogus = replace(result, solver_run_id=9_999_999_999)
    out = attach_optimization_replay_frames_after_successful_replay_build(bogus, _one_valid_frame())
    assert out.attached is False and out.reason == "solver_run_not_found"


def test_persist_skips_when_truncation_contract_breaks_on_serialized_blob() -> None:
    code = _encode_v4_copy(_minimal_root(version=612))
    dto = project_service.create_project_from_copy_code(code, source_label="trunc-skip")
    result = build_initial_replay_for_map_input(dto.map_input_id)
    assert result.status == "ok"
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    before = dict(run.config_json or {})
    bad = (
        OptimizationReplayFrame(
            frame_index=0,
            event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
            title="t",
            description="",
            visible_cells=(Coord(1, 0),),
            overlay_cells=(),
            metrics={"replay_truncated": True},
        ),
    )
    persist_optimization_replay_frames_to_solver_run(run, bad)
    run.refresh_from_db()
    assert run.config_json == before


def test_attach_invalid_replay_payload_when_truncation_pair_missing() -> None:
    code = _encode_v4_copy(_minimal_root(version=613))
    dto = project_service.create_project_from_copy_code(code, source_label="invalid-pair")
    result = build_initial_replay_for_map_input(dto.map_input_id)
    assert result.status == "ok"
    bad = (
        OptimizationReplayFrame(
            frame_index=0,
            event_type=OptimizationReplayEventType.CANDIDATE_GENERATED,
            title="t",
            description="",
            visible_cells=(Coord(1, 0),),
            overlay_cells=(),
            metrics={"replay_truncated": True},
        ),
    )
    out = attach_optimization_replay_frames_after_successful_replay_build(result, bad)
    assert out.attached is False and out.reason == "invalid_replay_payload"


def test_persisted_optimization_replay_invalid_shape_falls_back_empty() -> None:
    code = _encode_v4_copy(_minimal_root(version=614))
    dto = project_service.create_project_from_copy_code(code, source_label="bad-shape")
    result = build_initial_replay_for_map_input(dto.map_input_id)
    assert result.status == "ok"
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    merged = dict(run.config_json or {})
    merged[SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY] = {"not": "a list"}
    run.config_json = merged
    run.save(update_fields=["config_json"])
    ctx = alc.lab_page_context(project_id=dto.project_id)
    expected = empty_optimization_replay_track_payload_with_diagnostic(
        "invalid_optimization_replay_payload"
    )
    assert ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] == expected


def test_page_context_malformed_optimization_replay_does_not_crash() -> None:
    code = _encode_v4_copy(_minimal_root(version=615))
    dto = project_service.create_project_from_copy_code(code, source_label="mal-crash")
    result = build_initial_replay_for_map_input(dto.map_input_id)
    assert result.status == "ok"
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    merged = dict(run.config_json or {})
    merged[SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY] = None
    run.config_json = merged
    run.save(update_fields=["config_json"])
    ctx = alc.lab_page_context(project_id=dto.project_id)
    assert ctx[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] == (
        empty_optimization_replay_track_payload_with_diagnostic(
            "invalid_optimization_replay_payload"
        )
    )
