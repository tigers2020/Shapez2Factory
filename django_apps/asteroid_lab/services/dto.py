"""Service boundary DTOs (no Django imports).

Replay rows, playback sessions, and topology payloads are **persistence / cache / UI inspection
only**. They must **never** be read back as solver algorithm input; the solver engine stays a
pure DTO consumer over in-memory structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CreateProjectFromCopyCodeResultDTO:
    """Result of persisting a new lab project seeded from raw copy text."""

    project_id: int
    slug: str
    name: str
    map_input_id: int
    copy_code_sha256: str
    source_label: str


@dataclass(frozen=True, slots=True)
class SolverRunDTO:
    """One persisted lab solver run row (for UI / bookkeeping; not passed into solver core).

    ``replay_track_id`` is the default empty ``ReplayTrack`` shell for this run (UI timeline
    container only; never solver algorithm input).
    """

    id: int
    project_id: int
    run_key: str
    algorithm_label: str
    status: str
    config_json: dict[str, Any]
    replay_track_id: int


@dataclass(frozen=True, slots=True)
class ReplayFrameAppendDTO:
    """Incoming frame to append to a replay track (UI timeline; not solver input)."""

    frame_key: str
    phase: str
    title: str
    description: str = ""
    frame_payload: dict[str, Any] = field(default_factory=dict)
    cell_overlay_json: dict[str, Any] = field(default_factory=dict)
    metric_snapshot_json: dict[str, Any] = field(default_factory=dict)
    is_placeholder: bool = False
    is_keyframe: bool = False
    frame_index: int | None = None
    """If ``None``, next monotonic index is used. If set, must equal that next index."""


# Alias for API/docs that refer to a single "replay frame" append payload.
ReplayFrameDTO = ReplayFrameAppendDTO


@dataclass(frozen=True, slots=True)
class ReplayFrameRowDTO:
    """One stored replay frame row for UI payloads."""

    id: int
    frame_index: int
    frame_key: str
    phase: str
    title: str
    description: str
    frame_payload: dict[str, Any]
    cell_overlay_json: dict[str, Any]
    metric_snapshot_json: dict[str, Any]
    is_placeholder: bool
    is_keyframe: bool


@dataclass(frozen=True, slots=True)
class ReplayTrackPayloadDTO:
    """Ordered replay timeline for UI (inspection / playback only; not solver input)."""

    track_id: int
    project_id: int
    solver_run_id: int | None
    track_key: str
    title: str
    frames: tuple[ReplayFrameRowDTO, ...]


@dataclass(frozen=True, slots=True)
class ReplayTrackRefDTO:
    """Lightweight replay track handle after orchestration."""

    track_id: int
    project_id: int
    solver_run_id: int | None
    track_key: str


@dataclass(frozen=True, slots=True)
class PlaybackPatchDTO:
    """Partial update for ``UIPlaybackSession`` (client transport state only)."""

    current_frame_index: int | None = None
    is_playing: bool | None = None
    playback_speed_ms: int | None = None
    selected_layer: str | None = None
    selected_candidate_id: str | None = None
    selected_bundle_id: str | None = None
    ui_state_json: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class PlaybackSessionDTO:
    """Current persisted playback transport state (UI only)."""

    replay_track_id: int
    current_frame_index: int
    is_playing: bool
    playback_speed_ms: int
    selected_layer: str
    selected_candidate_id: str
    selected_bundle_id: str
    ui_state_json: dict[str, Any]


@dataclass(frozen=True, slots=True)
class TopologyRuleSummaryDTO:
    """Catalog row shown beside modal content."""

    rule_key: str
    title: str
    short_label: str
    rule_group: str
    severity: str
    description: str
    examples_json: list[Any]
    diagram_json: dict[str, Any]
    is_active: bool
    sort_order: int


@dataclass(frozen=True, slots=True)
class TopologyModalBodyDTO:
    """Rich modal body (UI only)."""

    modal_title: str
    lead_html: str
    sections_json: list[Any]
    footer_json: dict[str, Any]


@dataclass(frozen=True, slots=True)
class TopologyModalPayloadDTO:
    """Joined rule + modal content for topology help UI."""

    rule: TopologyRuleSummaryDTO
    modal: TopologyModalBodyDTO


@dataclass(frozen=True, slots=True)
class TopologyModalResultDTO:
    """Structured lookup result (HTTP layer may map ``not_found`` to 404)."""

    found: bool
    error_code: str
    message: str
    payload: TopologyModalPayloadDTO | None = None


@dataclass(frozen=True, slots=True)
class RawDecodedBlueprintDTO:
    """Validated root JSON from :func:`decode_copy_string` (no lab summary block yet)."""

    root: dict[str, Any]


@dataclass(frozen=True, slots=True)
class NormalizedBlueprintDTO:
    """Blueprint JSON ready to persist on ``AsteroidMapInput.decoded_json``."""

    decoded_json: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SnapshotEventDTO:
    """One logical solver/UI step emitted for replay (never solver algorithm input)."""

    event_key: str
    phase: str
    phase_step: str = ""
    event_type: str = ""
    title: str = ""
    description: str = ""
    before_state_json: dict[str, Any] = field(default_factory=dict)
    after_state_json: dict[str, Any] = field(default_factory=dict)
    delta_json: dict[str, Any] = field(default_factory=dict)
    cell_overlay_json: dict[str, Any] = field(default_factory=dict)
    focus_cells_json: list[Any] = field(default_factory=list)
    candidate_ref: str = ""
    bundle_ref: str = ""
    route_ref: str = ""
    is_decision_point: bool = False
    is_reversible: bool = True
    is_placeholder: bool = False
    severity: str = "info"
    metrics_json: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SnapshotFrameDTO:
    """Result row after persisting a snapshot as ``ReplayFrame`` (UI playback artifact)."""

    replay_frame_id: int
    replay_track_id: int
    frame_index: int
    event_key: str
    phase: str
    event_type: str
    title: str
    frame_payload: dict[str, Any]
    cell_overlay_json: dict[str, Any]
    metric_snapshot_json: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ReplayRecordingPolicyDTO:
    """Optional thinning / caps for replay volume (does not affect solver correctness)."""

    capture_every_step: bool = True
    capture_rejected_candidates: bool = True
    capture_probe_paths: bool = True
    capture_before_after: bool = True
    max_frames: int | None = None
    thinning_strategy: str = "none"
