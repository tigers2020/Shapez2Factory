"""Layer 04 rim provisional placement runtime replay segment (transient overlay specs only)."""

from __future__ import annotations

from collections.abc import Sequence

from django_apps.asteroid_lab.replay.event_types import assert_registered_event_type
from django_apps.asteroid_lab.replay.pattern_bundle_highlight import (
    METRICS_KEY,
    build_pattern_bundle_highlights_wire,
    mining_occupied_from_rim_placement,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.replay_limits import (
    MAX_LAYER04_REPLAY_REJECTED_OVERLAP,
    MAX_LAYER04_REPLAY_SELECTED,
)
from django_apps.asteroid_lab.replay.segment_frame_spec import ReplaySegmentFrameSpec
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayOverlayCell
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import BundleCellRole
from shapez2_factory.application.asteroid_lab.layers.contracts.placement_state import (
    PlacementCommitState,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_placement import (
    Layer04PackingObservability,
    RimBundlePlacement,
    RimPlacementRejection,
    RimPlacementRejectReason,
)

LAYER04_PHASE = "layer_04_rim_bundle_placement"
LAYER04_INSPECTOR_STEP = "layer_04_rim_bundle_placement"
OVERLAY_KIND_ROUTE_PROBE_PATH = "route_probe_path"

_L4_INSPECTOR = {
    "lab_phase": "candidate_generation",
    "lab_phase_step": LAYER04_INSPECTOR_STEP,
}


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


def _pattern_bundle_highlights_for_placement(
    placement: RimBundlePlacement,
) -> dict[str, object]:
    occupied = mining_occupied_from_rim_placement(placement)
    return build_pattern_bundle_highlights_wire(
        ((placement.candidate_id, occupied, placement.gene_key),)
    )


def _pattern_bundle_highlights_for_placements(
    placements: Sequence[RimBundlePlacement],
) -> dict[str, object]:
    entries = [
        (
            placement.candidate_id,
            mining_occupied_from_rim_placement(placement),
            placement.gene_key,
        )
        for placement in placements
    ]
    return build_pattern_bundle_highlights_wire(entries)


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


def _overlay_kind_for_cell_role(cell_role: BundleCellRole, *, transport: str) -> str:
    return _overlay_kind_for_role(role=cell_role.value, transport=transport)


def _overlay_cells_from_bundle_cell_placements(
    placement: RimBundlePlacement,
) -> tuple[ReplayOverlayCell, ...]:
    transport = placement.transport_kind.value
    overlay: list[ReplayOverlayCell] = []
    for cell in placement.cell_placements:
        x, y = cell.coord
        overlay.append(
            ReplayOverlayCell(
                x=x,
                y=y,
                kind=_overlay_kind_for_cell_role(cell.cell_role, transport=transport),
                transport=transport,
                tile_type=cell.layout_t,
                rotation=cell.rotation,
            )
        )
    return tuple(overlay)


def _overlay_cells_for_placement_legacy(
    placement: RimBundlePlacement,
) -> tuple[ReplayOverlayCell, ...]:
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


def _overlay_route_probe_path_cells(
    placement: RimBundlePlacement,
) -> tuple[ReplayOverlayCell, ...]:
    if not placement.probed_route_path_cells:
        return ()
    transport = placement.transport_kind.value
    return tuple(
        ReplayOverlayCell(
            x=x,
            y=y,
            kind=OVERLAY_KIND_ROUTE_PROBE_PATH,
            transport=transport,
        )
        for x, y in placement.probed_route_path_cells
    )


def _overlay_cells_for_placement(placement: RimBundlePlacement) -> tuple[ReplayOverlayCell, ...]:
    if placement.cell_placements:
        placement_cells = _overlay_cells_from_bundle_cell_placements(placement)
    else:
        placement_cells = _overlay_cells_for_placement_legacy(placement)
    return placement_cells + _overlay_route_probe_path_cells(placement)


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


def _spec(
    *,
    event_type: ReplayEventType,
    title: str,
    description: str,
    metrics: dict[str, object],
    transient_overlay_cells: tuple[ReplayOverlayCell, ...] = (),
) -> ReplaySegmentFrameSpec:
    assert_registered_event_type(event_type.value)
    return ReplaySegmentFrameSpec(
        event_type=event_type,
        phase=ReplayPhase.CANDIDATE_GENERATION,
        title=title,
        description=description,
        metrics=metrics,
        transient_overlay_cells=transient_overlay_cells,
        inspector={**_L4_INSPECTOR, "lab_event_type": event_type.value},
    )


def _packing_observability_metrics(
    observability: Layer04PackingObservability | None,
) -> dict[str, object]:
    if observability is None:
        return {}
    metrics: dict[str, object] = {
        "selected_total_gain": observability.selected_total_gain,
        "budget_limited": observability.budget_limited,
    }
    if observability.greedy_baseline_total_gain is not None:
        metrics["greedy_baseline_total_gain"] = observability.greedy_baseline_total_gain
    if observability.greedy_baseline_skipped_reason is not None:
        metrics["greedy_baseline_skipped_reason"] = observability.greedy_baseline_skipped_reason
    if observability.budget_interrupted_component_id is not None:
        metrics["budget_interrupted_component_id"] = observability.budget_interrupted_component_id
    if observability.component_records:
        metrics["packing_component_count"] = len(observability.component_records)
        first = observability.component_records[0]
        metrics["selection_strategy"] = first.selection_strategy.value
        metrics["packing_component_id"] = first.component_id
    return metrics


def build_layer04_runtime_segment_specs(
    *,
    selected: tuple[RimBundlePlacement, ...],
    rejected: tuple[RimPlacementRejection, ...],
    packing_observability: Layer04PackingObservability | None = None,
) -> tuple[ReplaySegmentFrameSpec, ...]:
    """Transient L4 observation specs; assembler composes persistent exterior overlays."""

    frames: list[ReplaySegmentFrameSpec] = [
        _spec(
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
        highlights = _pattern_bundle_highlights_for_placement(placement)
        if highlights:
            meta[METRICS_KEY] = highlights
        frames.append(
            _spec(
                event_type=ReplayEventType.LAYER04_RIM_CANDIDATE_SELECTED,
                title="Layer 04 candidate selected",
                description=f"Provisional placement {placement.candidate_id}",
                metrics=meta,
                transient_overlay_cells=_overlay_cells_for_placement(placement),
            )
        )

    for rejection in rejections_for_replay:
        frames.append(
            _spec(
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
                transient_overlay_cells=_overlay_cells_for_overlap_rejection(rejection),
            )
        )

    complete_metrics: dict[str, object] = {
        "layer": LAYER04_PHASE,
        "selected_count": len(selected),
        "rejected_count": len(rejected),
        "rejected_overlap_count": len(overlap_rejections),
        **_packing_observability_metrics(packing_observability),
    }
    if truncated_selected:
        complete_metrics["truncated_selected_replay"] = True
        complete_metrics["replay_selected_cap"] = MAX_LAYER04_REPLAY_SELECTED
    if truncated_rejected:
        complete_metrics["truncated_rejected_overlap_replay"] = True
        complete_metrics["replay_rejected_overlap_cap"] = MAX_LAYER04_REPLAY_REJECTED_OVERLAP
        complete_metrics["rejected_overlap_replay_shown"] = len(rejections_for_replay)

    complete_highlights = _pattern_bundle_highlights_for_placements(selected)
    if complete_highlights:
        complete_metrics[METRICS_KEY] = complete_highlights

    frames.append(
        _spec(
            event_type=ReplayEventType.LAYER04_RIM_PLACEMENT_COMPLETE,
            title="Layer 04 rim placement complete",
            description=(
                f"Selected {len(selected)} placement(s); "
                f"{len(overlap_rejections)} overlap rejection(s) recorded"
            ),
            metrics=complete_metrics,
            transient_overlay_cells=_combined_overlay_for_placements(selected),
        )
    )
    return tuple(frames)


__all__ = [
    "LAYER04_INSPECTOR_STEP",
    "LAYER04_PHASE",
    "OVERLAY_KIND_ROUTE_PROBE_PATH",
    "build_layer04_runtime_segment_specs",
]
