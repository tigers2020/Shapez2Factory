"""Layer 02 solver timeline frame builder (append-stack; output-only)."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.replay.layer02_segment import (
    LAYER02_EVENT_TYPE,
    LAYER02_INSPECTOR_STEP,
    build_layer02_exterior_transport_frame,
    build_layer02_timeline_frame_wire_dict,
)
from django_apps.asteroid_lab.replay.reconstruction_source import (
    find_reconstruction_complete_source_frame,
)
from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
    build_solver_runtime_replay_frames,
)


def resolve_l2_complete_frame_index(
    frames: list[dict[str, object]],
    *,
    explicit_index: int | None = None,
) -> int | None:
    """Index of first frame that should show L2 overlay; None when L2 is not on the timeline."""

    if explicit_index is not None and explicit_index >= 0:
        return explicit_index
    for index, frame in enumerate(frames):
        if frame.get("event_type") == LAYER02_EVENT_TYPE.value:
            return index
    return None


def build_layer02_timeline_frame_dict(
    *,
    plan_wire: dict[str, object],
    source_frame: dict[str, object] | None,
    complete_map: ReconstructionCompleteMap | None,
) -> dict[str, object]:
    """One append-stack milestone: L1 full map + L2 planned connector overlay only."""

    return build_layer02_timeline_frame_wire_dict(
        plan_wire=plan_wire,
        source_frame=source_frame,
        complete_map=complete_map,
    )


def build_layer02_runtime_replay_frames(
    *,
    plan_wire: dict[str, object],
    lab_frames_before_append: list[dict[str, object]],
    complete_map: ReconstructionCompleteMap,
) -> list[dict[str, object]]:
    """Deprecated: use ``replay.solver_runtime_assembler.build_solver_runtime_replay_frames``."""

    return build_solver_runtime_replay_frames(
        complete_map=complete_map,
        lab_frames_before_append=lab_frames_before_append,
        exterior_plan_wire=plan_wire,
        layer03=None,
        layer04=None,
    )


__all__ = [
    "LAYER02_EVENT_TYPE",
    "LAYER02_INSPECTOR_STEP",
    "build_layer02_exterior_transport_frame",
    "build_layer02_runtime_replay_frames",
    "build_layer02_timeline_frame_dict",
    "build_solver_runtime_replay_frames",
    "find_reconstruction_complete_source_frame",
    "resolve_l2_complete_frame_index",
]
