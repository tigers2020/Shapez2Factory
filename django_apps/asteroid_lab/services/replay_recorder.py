"""A4 replay-first capture: ``SnapshotEventDTO`` → ``ReplayFrame`` (append-only UI artifact).

This module **writes** timeline rows only. It does not load ordered replay payloads from the
database for use as solver decisions.
"""

from __future__ import annotations

from dataclasses import asdict

from django.db import transaction

from django_apps.asteroid_lab.models import ReplayFrame
from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_CANDIDATE_REJECTED,
    EVENT_TYPE_ROUTING_PATH_PREVIEWED,
    assert_registered_event_type,
)
from django_apps.asteroid_lab.services.dto import (
    ReplayFrameAppendDTO,
    ReplayRecordingPolicyDTO,
    SnapshotEventDTO,
    SnapshotFrameDTO,
)
from django_apps.asteroid_lab.services.replay_service import (
    append_replay_frame,
    next_replay_frame_index,
)


class ReplayRecorderCapExceeded(Exception):
    """Raised when ``ReplayRecordingPolicyDTO.max_frames`` would be exceeded."""


class ReplayRecorder:
    """Persists :class:`SnapshotEventDTO` as ``ReplayFrame`` rows (output-only artifact)."""

    def __init__(self, track_id: int, policy: ReplayRecordingPolicyDTO | None = None) -> None:
        self._track_id = int(track_id)
        self._policy = policy or ReplayRecordingPolicyDTO()

    def next_frame_index(self) -> int:
        return next_replay_frame_index(self._track_id)

    def _should_skip_for_policy(self, event: SnapshotEventDTO) -> bool:
        p = self._policy
        if not p.capture_rejected_candidates and event.event_type == EVENT_TYPE_CANDIDATE_REJECTED:
            return True
        if not p.capture_probe_paths and event.event_type == EVENT_TYPE_ROUTING_PATH_PREVIEWED:
            return True
        if not p.capture_every_step and not event.is_decision_point:
            return True
        return False

    def _payload_dict(self, event: SnapshotEventDTO) -> dict[str, object]:
        body: dict[str, object] = asdict(event)
        if not self._policy.capture_before_after:
            body["before_state_json"] = {}
            body["after_state_json"] = {}
            body["delta_json"] = {}
        return body

    def _enforce_max_frames(self) -> None:
        m = self._policy.max_frames
        if m is None:
            return
        count = ReplayFrame.objects.filter(replay_track_id=self._track_id).count()
        if count >= m:
            msg = f"ReplayRecorder max_frames={m} reached for track_id={self._track_id}"
            raise ReplayRecorderCapExceeded(msg)

    def record_event(self, event: SnapshotEventDTO) -> SnapshotFrameDTO | None:
        assert_registered_event_type(event.event_type)
        if self._should_skip_for_policy(event):
            return None
        self._enforce_max_frames()
        payload = self._payload_dict(event)
        append_dto = ReplayFrameAppendDTO(
            frame_key=event.event_key,
            phase=event.phase,
            title=event.title,
            description=event.description,
            frame_payload=payload,
            cell_overlay_json=dict(event.cell_overlay_json or {}),
            metric_snapshot_json=dict(event.metrics_json or {}),
            is_placeholder=event.is_placeholder,
            is_keyframe=event.is_decision_point,
        )
        row = append_replay_frame(self._track_id, append_dto)
        return SnapshotFrameDTO(
            replay_frame_id=row.id,
            replay_track_id=self._track_id,
            frame_index=row.frame_index,
            event_key=event.event_key,
            phase=event.phase,
            event_type=event.event_type,
            title=event.title,
            frame_payload=dict(row.frame_payload or {}),
            cell_overlay_json=dict(row.cell_overlay_json or {}),
            metric_snapshot_json=dict(row.metric_snapshot_json or {}),
        )

    def record_many(self, events: list[SnapshotEventDTO]) -> list[SnapshotFrameDTO]:
        out: list[SnapshotFrameDTO] = []
        with transaction.atomic():
            for ev in events:
                got = self.record_event(ev)
                if got is not None:
                    out.append(got)
        return out
