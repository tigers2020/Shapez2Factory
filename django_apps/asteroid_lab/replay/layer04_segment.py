"""Layer 04 rim provisional placement runtime replay segment (projection only)."""

from __future__ import annotations

from collections.abc import Sequence

from django_apps.asteroid_lab.layers.contracts.placement_state import PlacementCommitState
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    RimBundlePlacement,
    RimPlacementRejection,
    RimPlacementRejectReason,
)
from django_apps.asteroid_lab.replay.event_types import assert_registered_event_type
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.replay_limits import (
    MAX_LAYER04_REPLAY_REJECTED_OVERLAP,
    MAX_LAYER04_REPLAY_SELECTED,
)
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayMapView,
    ReplayOverlayCell,
    ReplayTimelineFrame,
    replay_map_view_is_renderable,
)
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_map_view_from_json_dict,
    replay_map_view_to_json_dict,
)

LAYER04_PHASE = "layer_04_rim_bundle_placement"
LAYER04_INSPECTOR_STEP = "layer_04_rim_bundle_placement"


def _copy_map_view(base_map_view: ReplayMapView) -> ReplayMapView:
    return replay_map_view_from_json_dict(replay_map_view_to_json_dict(base_map_view))


def _overlay_kind_for_role(*, role: str, transport: str) -> str:
    """Map L4 observation role to domain cell_kind for Lab sprite resolution."""
    is_fluid = transport == "fluid_pipe"
    if role == "miner":
        return "fluid_miner" if is_fluid else "shape_miner"
    if role == "extension":
        return "fluid_miner_extension" if is_fluid else "shape_miner_extension"
    if role == "transport_stub":
        return "space_pipe" if is_fluid else "space_belt"
    return role


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


def _overlay_cells_for_placement(placement: RimBundlePlacement) -> tuple[ReplayOverlayCell, ...]:
    transport = placement.transport_kind.value
    overlay: list[ReplayOverlayCell] = []
    for x, y in sorted(placement.extractor_cells):
        overlay.append(
            ReplayOverlayCell(
                x=x,
                y=y,
                kind=_overlay_kind_for_role(role="miner", transport=transport),
                transport=transport,
            )
        )
    for x, y in sorted(placement.extension_cells):
        overlay.append(
            ReplayOverlayCell(
                x=x,
                y=y,
                kind=_overlay_kind_for_role(role="extension", transport=transport),
                transport=transport,
            )
        )
    for x, y in sorted(placement.output_stub_cells):
        overlay.append(
            ReplayOverlayCell(
                x=x,
                y=y,
                kind=_overlay_kind_for_role(role="transport_stub", transport=transport),
                transport=transport,
            )
        )
    return tuple(overlay)


def _overlay_cells_for_overlap_rejection(
    rejection: RimPlacementRejection,
) -> tuple[ReplayOverlayCell, ...]:
    if not rejection.conflicting_cells:
        return ()
    return tuple(
        ReplayOverlayCell(x=x, y=y, kind="overlap_conflict", transport="")
        for x, y in sorted(rejection.conflicting_cells)
    )


def _combined_overlay_for_placements(
    placements: Sequence[RimBundlePlacement],
) -> tuple[ReplayOverlayCell, ...]:
    combined: list[ReplayOverlayCell] = []
    for placement in placements:
        combined.extend(_overlay_cells_for_placement(placement))
    return tuple(combined)


def _timeline_frame(
    *,
    base_map_view: ReplayMapView,
    event_type: ReplayEventType,
    title: str,
    description: str,
    metrics: dict[str, object],
    overlay_cells: tuple[ReplayOverlayCell, ...] = (),
) -> ReplayTimelineFrame:
    assert_registered_event_type(event_type.value)
    map_view = _copy_map_view(base_map_view)
    if overlay_cells:
        existing = list(map_view.overlay_cells)
        existing.extend(overlay_cells)
        map_view = ReplayMapView(
            bbox=map_view.bbox,
            base_ref=map_view.base_ref,
            full_cells=map_view.full_cells,
            cell_delta=map_view.cell_delta,
            overlay_cells=tuple(existing),
            annotations=map_view.annotations,
        )
    if not replay_map_view_is_renderable(map_view):
        msg = "layer04 segment frame must be renderable"
        raise ValueError(msg)
    return ReplayTimelineFrame(
        frame_index=0,
        phase=ReplayPhase.CANDIDATE_GENERATION,
        event_type=event_type,
        title=title,
        description=description,
        map_view=map_view,
        inspector={
            "lab_phase": "candidate_generation",
            "lab_phase_step": LAYER04_INSPECTOR_STEP,
            "lab_event_type": event_type.value,
        },
        metrics=metrics,
    )


def build_layer04_runtime_segment_frames(
    *,
    base_map_view: ReplayMapView,
    selected: tuple[RimBundlePlacement, ...],
    rejected: tuple[RimPlacementRejection, ...],
) -> tuple[ReplayTimelineFrame, ...]:
    """Build L4 runtime segment frames; ``base_map_view`` is assembler-owned only."""

    frames: list[ReplayTimelineFrame] = [
        _timeline_frame(
            base_map_view=base_map_view,
            event_type=ReplayEventType.LAYER04_RIM_PLACEMENT_BEGIN,
            title="Layer 04 rim placement begin",
            description="Layer 04 rim bundle provisional placement",
            metrics={"layer": LAYER04_PHASE},
        )
    ]

    truncated_selected = len(selected) > MAX_LAYER04_REPLAY_SELECTED
    selected_for_replay = selected[:MAX_LAYER04_REPLAY_SELECTED]

    overlap_rejections = tuple(
        r for r in rejected if r.reason is RimPlacementRejectReason.PHYSICAL_OVERLAP
    )
    truncated_rejected = len(overlap_rejections) > MAX_LAYER04_REPLAY_REJECTED_OVERLAP
    rejections_for_replay = overlap_rejections[:MAX_LAYER04_REPLAY_REJECTED_OVERLAP]

    for placement in selected_for_replay:
        meta = _placement_metadata(placement)
        frames.append(
            _timeline_frame(
                base_map_view=base_map_view,
                event_type=ReplayEventType.LAYER04_RIM_CANDIDATE_SELECTED,
                title="Layer 04 candidate selected",
                description=f"Provisional placement {placement.candidate_id}",
                metrics=meta,
                overlay_cells=_overlay_cells_for_placement(placement),
            )
        )

    for rejection in rejections_for_replay:
        frames.append(
            _timeline_frame(
                base_map_view=base_map_view,
                event_type=ReplayEventType.LAYER04_RIM_CANDIDATE_REJECTED_OVERLAP,
                title="Layer 04 candidate rejected (overlap)",
                description=f"Rejected {rejection.candidate_id}",
                metrics={
                    "layer": LAYER04_PHASE,
                    "candidate_id": rejection.candidate_id,
                    "equivalence_key": rejection.equivalence_key,
                    "reason": rejection.reason.value,
                    "conflicting_candidate_id": rejection.conflicting_candidate_id,
                    "conflicting_cell_count": len(rejection.conflicting_cells),
                },
                overlay_cells=_overlay_cells_for_overlap_rejection(rejection),
            )
        )

    complete_metrics: dict[str, object] = {
        "layer": LAYER04_PHASE,
        "selected_count": len(selected),
        "rejected_count": len(rejected),
        "rejected_overlap_count": len(overlap_rejections),
    }
    if truncated_selected:
        complete_metrics["truncated_selected_replay"] = True
        complete_metrics["replay_selected_cap"] = MAX_LAYER04_REPLAY_SELECTED
    if truncated_rejected:
        complete_metrics["truncated_rejected_overlap_replay"] = True
        complete_metrics["replay_rejected_overlap_cap"] = MAX_LAYER04_REPLAY_REJECTED_OVERLAP
        complete_metrics["rejected_overlap_replay_shown"] = len(rejections_for_replay)

    frames.append(
        _timeline_frame(
            base_map_view=base_map_view,
            event_type=ReplayEventType.LAYER04_RIM_PLACEMENT_COMPLETE,
            title="Layer 04 rim placement complete",
            description=(
                f"Selected {len(selected)} placement(s); "
                f"{len(overlap_rejections)} overlap rejection(s) recorded"
            ),
            metrics=complete_metrics,
            overlay_cells=_combined_overlay_for_placements(selected),
        )
    )
    return tuple(frames)


__all__ = [
    "LAYER04_INSPECTOR_STEP",
    "LAYER04_PHASE",
    "build_layer04_runtime_segment_frames",
]
