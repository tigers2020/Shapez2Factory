"""Phase 9A — Lab replay timeline DTO contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayAnnotation,
    ReplayBBox,
    ReplayCell,
    ReplayCellDelta,
    ReplayMapView,
    ReplayOverlayCell,
    ReplayTimelineFrame,
    replay_map_view_is_renderable,
)
from django_apps.asteroid_lab.replay.timeline_serialization import (
    ReplayTimelineDeserializationError,
    parse_replay_event_type,
    replay_timeline_frame_from_json_dict,
    replay_timeline_frame_json_round_trip,
    replay_timeline_frame_to_json_dict,
)

_REPLAY_PKG = Path(__file__).resolve().parents[3] / "django_apps" / "asteroid_lab" / "replay"

_FORBIDDEN_IMPORT_FRAGMENTS = (
    "django_apps.asteroid_lab.models",
    "django_apps.asteroid_lab.services.replay_service",
    "django_apps.asteroid_lab.services.optimization_replay_persist",
    "django_apps.asteroid_lab.services.solver_runtime_pipeline",
    "django_apps.asteroid_lab.services.solver_runtime_entry",
    "django_apps.asteroid_lab.services.runtime_replay_recorder",
)

_EXPECTED_PHASE_VALUES = (
    "decode",
    "reconstruction",
    "optimization_input",
    "pattern_generation",
    "candidate_generation",
    "route_probe",
    "genome_fitness",
    "evolution",
    "incremental_commit",
    "rollback",
    "validation",
    "result",
)

_EXPECTED_EVENT_TYPE_VALUES = tuple(m.value for m in ReplayEventType)


def _bbox() -> ReplayBBox:
    return ReplayBBox(min_x=0, min_y=0, max_x=10, max_y=10)


def _sample_frame(*, map_view: ReplayMapView) -> ReplayTimelineFrame:
    return ReplayTimelineFrame(
        frame_index=0,
        phase=ReplayPhase.DECODE,
        event_type=ReplayEventType.DECODE_STARTED,
        title="t",
        description="d",
        map_view=map_view,
    )


def test_replay_phase_enum_values_fixed() -> None:
    assert tuple(m.value for m in ReplayPhase) == _EXPECTED_PHASE_VALUES


def test_replay_event_type_enum_values_fixed() -> None:
    assert _EXPECTED_EVENT_TYPE_VALUES == tuple(m.value for m in ReplayEventType)
    assert ReplayEventType.ROUTE_PROBE_SUCCEEDED.value == "route_probe.succeeded"
    assert ReplayEventType.CAPACITY_PLAN_CREATED.value == "capacity.plan_created"


def test_replay_timeline_dtos_are_immutable() -> None:
    frame = _sample_frame(
        map_view=ReplayMapView(
            bbox=_bbox(),
            full_cells=(ReplayCell(x=1, y=2, kind="asteroid"),),
        )
    )
    with pytest.raises(AttributeError):
        frame.frame_index = 99  # type: ignore[misc]


def test_unified_replay_frame_requires_map_view_field() -> None:
    with pytest.raises(TypeError):
        ReplayTimelineFrame(  # type: ignore[call-arg]
            frame_index=0,
            phase=ReplayPhase.DECODE,
            event_type=ReplayEventType.DECODE_STARTED,
            title="t",
            description="d",
        )


def test_parse_replay_event_type_rejects_arbitrary_string() -> None:
    with pytest.raises(ReplayTimelineDeserializationError):
        parse_replay_event_type("not.a.real.event")


def test_unified_replay_frame_index_is_int() -> None:
    mv = ReplayMapView(bbox=_bbox(), overlay_cells=(ReplayOverlayCell(x=1, y=1),))
    frame = _sample_frame(map_view=mv)
    assert isinstance(frame.frame_index, int)
    payload = replay_timeline_frame_to_json_dict(frame)
    with pytest.raises(ReplayTimelineDeserializationError):
        replay_timeline_frame_from_json_dict({**payload, "frame_index": "0"})


def test_map_view_full_snapshot_is_renderable() -> None:
    mv = ReplayMapView(
        bbox=_bbox(),
        full_cells=(ReplayCell(x=1, y=1, kind="asteroid", transport="none"),),
    )
    assert replay_map_view_is_renderable(mv)


def test_map_view_overlay_only_is_renderable() -> None:
    mv = ReplayMapView(
        bbox=_bbox(),
        base_ref="reconstruction_complete",
        overlay_cells=(ReplayOverlayCell(x=12, y=5, kind="route_probe_path"),),
        annotations=(ReplayAnnotation(x=20, y=5, label="goal"),),
    )
    assert replay_map_view_is_renderable(mv)


def test_map_view_commit_delta_is_renderable() -> None:
    mv = ReplayMapView(
        bbox=_bbox(),
        cell_delta=(ReplayCellDelta(x=3, y=4, kind="transport", transport="shape_belt"),),
    )
    assert replay_map_view_is_renderable(mv)


def test_metadata_only_map_view_is_not_renderable() -> None:
    mv = ReplayMapView(bbox=_bbox())
    assert not replay_map_view_is_renderable(mv)


def test_replay_timeline_frame_json_round_trip() -> None:
    frame = ReplayTimelineFrame(
        frame_index=42,
        phase=ReplayPhase.ROUTE_PROBE,
        event_type=ReplayEventType.ROUTE_PROBE_SUCCEEDED,
        title="Route probe succeeded",
        description="Candidate reached margin.",
        map_view=ReplayMapView(
            base_ref="reconstruction_complete",
            overlay_cells=(
                ReplayOverlayCell(x=12, y=5, kind="route_probe_path", transport="shape_belt"),
            ),
            annotations=(ReplayAnnotation(x=20, y=5, label="external goal"),),
            bbox=ReplayBBox(min_x=10, min_y=4, max_x=22, max_y=7),
        ),
        inspector={"candidate_id": "cand_017"},
        metrics={"goal_priority": 2},
    )
    restored = replay_timeline_frame_json_round_trip(frame)
    assert restored == frame


def test_unified_replay_serialization_is_json_safe() -> None:
    frame = _sample_frame(map_view=ReplayMapView(bbox=_bbox(), full_cells=(ReplayCell(x=0, y=0),)))
    payload = replay_timeline_frame_to_json_dict(frame)
    text = json.dumps(payload, default=str)
    parsed = json.loads(text)
    assert isinstance(parsed, dict)
    assert parsed["event_type"] == "decode.started"


def test_unified_replay_from_json_rejects_unknown_event_type() -> None:
    frame = _sample_frame(map_view=ReplayMapView(bbox=_bbox(), base_ref="k1"))
    payload = replay_timeline_frame_to_json_dict(frame)
    payload["event_type"] = "free.form.string"
    with pytest.raises(ReplayTimelineDeserializationError):
        replay_timeline_frame_from_json_dict(payload)


def test_unified_replay_from_json_requires_map_view() -> None:
    with pytest.raises(ReplayTimelineDeserializationError):
        replay_timeline_frame_from_json_dict(
            {
                "frame_index": 0,
                "phase": "decode",
                "event_type": "decode.started",
                "title": "",
                "description": "",
            }
        )


@pytest.mark.parametrize(
    "module_name",
    ["timeline_dtos.py", "replay_enums.py", "timeline_serialization.py"],
)
def test_unified_replay_modules_import_boundary(module_name: str) -> None:
    text = (_REPLAY_PKG / module_name).read_text(encoding="utf-8")
    for bad in _FORBIDDEN_IMPORT_FRAGMENTS:
        assert bad not in text, f"{module_name} must not reference {bad!r}"
