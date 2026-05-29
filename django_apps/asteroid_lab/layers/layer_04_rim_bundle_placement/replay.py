"""Layer 04 replay frame builders (observability only; not algorithm input)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.placement_state import PlacementCommitState
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    RimBundlePlacement,
    RimPlacementRejection,
    RimPlacementRejectReason,
)
from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_LAYER04_RIM_CANDIDATE_REJECTED_OVERLAP,
    EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED,
    EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN,
    EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE,
    assert_registered_event_type,
)
from django_apps.asteroid_lab.services.dto import ReplayFrameAppendDTO

LAYER04_PHASE = "layer_04_rim_bundle_placement"


def _placement_metadata(placement: RimBundlePlacement) -> dict[str, object]:
    x, y = placement.anchor_coord
    return {
        "layer": LAYER04_PHASE,
        "placement_state": PlacementCommitState.PROVISIONAL_PLACED.value,
        "candidate_id": placement.candidate_id,
        "equivalence_key": placement.equivalence_key,
        "gene_key": placement.gene_key,
        "transport_kind": placement.transport_kind.value,
        "anchor_coord": {"x": x, "y": y},
        "occupied_cell_count": len(placement.occupied_cells),
    }


def _frame(
    *,
    frame_key: str,
    event_type: str,
    title: str,
    metadata: dict[str, object],
) -> ReplayFrameAppendDTO:
    assert_registered_event_type(event_type)
    payload = {"event_type": event_type, **metadata}
    return ReplayFrameAppendDTO(
        frame_key=frame_key,
        phase=LAYER04_PHASE,
        title=title,
        frame_payload=payload,
    )


def build_layer04_replay_frames(
    *,
    selected: tuple[RimBundlePlacement, ...],
    rejected: tuple[RimPlacementRejection, ...],
) -> tuple[ReplayFrameAppendDTO, ...]:
    frames: list[ReplayFrameAppendDTO] = [
        _frame(
            frame_key="layer04:begin",
            event_type=EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN,
            title="Layer 04 rim placement begin",
            metadata={"layer": LAYER04_PHASE},
        )
    ]
    for placement in selected:
        meta = _placement_metadata(placement)
        frames.append(
            _frame(
                frame_key=f"layer04:selected:{placement.candidate_id}",
                event_type=EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED,
                title="Layer 04 candidate selected",
                metadata=meta,
            )
        )
    for rejection in rejected:
        if rejection.reason is not RimPlacementRejectReason.PHYSICAL_OVERLAP:
            continue
        frames.append(
            _frame(
                frame_key=f"layer04:rejected_overlap:{rejection.candidate_id}",
                event_type=EVENT_TYPE_LAYER04_RIM_CANDIDATE_REJECTED_OVERLAP,
                title="Layer 04 candidate rejected (overlap)",
                metadata={
                    "layer": LAYER04_PHASE,
                    "candidate_id": rejection.candidate_id,
                    "equivalence_key": rejection.equivalence_key,
                    "reason": rejection.reason.value,
                    "conflicting_candidate_id": rejection.conflicting_candidate_id,
                    "conflicting_cell_count": len(rejection.conflicting_cells),
                },
            )
        )
    frames.append(
        _frame(
            frame_key="layer04:complete",
            event_type=EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE,
            title="Layer 04 rim placement complete",
            metadata={
                "layer": LAYER04_PHASE,
                "selected_count": len(selected),
                "rejected_count": len(rejected),
            },
        )
    )
    return tuple(frames)


__all__ = ["build_layer04_replay_frames"]
