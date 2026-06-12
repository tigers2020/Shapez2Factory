"""Layer 04 inner pattern fill replay segment (canonical L4 slug)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.event_types import assert_registered_event_type
from django_apps.asteroid_lab.replay.overlay_wire_contract import build_output_hint_overlay_cell
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.segment_frame_spec import ReplaySegmentFrameSpec
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayOverlayCell
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    Layer04InnerFillResult,
    RouteableInnerGroupPlacement,
)

LAYER04_INNER_PATTERN_FILL_PHASE = "layer_04_inner_pattern_fill"
COMMITTED_INNER_FILL_OVERLAY_ROLE = "committed_inner_fill"

_L4_INNER_FILL_INSPECTOR = {
    "lab_phase": "pattern_generation",
    "lab_phase_step": LAYER04_INNER_PATTERN_FILL_PHASE,
}


def _miner_kind(*, transport_kind: str) -> str:
    return "fluid_miner" if transport_kind == "space_pipe" else "shape_miner"


def _extension_kind(*, transport_kind: str) -> str:
    return "fluid_miner_extension" if transport_kind == "space_pipe" else "shape_miner_extension"


def _overlay_cells_for_result(
    result: Layer04InnerFillResult,
    *,
    transport_kind: str,
) -> tuple[ReplayOverlayCell, ...]:
    miner_kind = _miner_kind(transport_kind=transport_kind)
    extension_kind = _extension_kind(transport_kind=transport_kind)
    cells: list[ReplayOverlayCell] = []

    for group in result.routeable_inner_groups:
        cells.extend(
            _overlays_for_routeable_group(
                group,
                miner_kind=miner_kind,
                extension_kind=extension_kind,
            )
        )

    seen: set[tuple[int, int]] = {(cell.x, cell.y) for cell in cells}
    for placement in result.placements:
        x, y = placement.coord
        if (x, y) in seen:
            continue
        seen.add((x, y))
        cells.append(
            build_output_hint_overlay_cell(
                x=x,
                y=y,
                kind="inner_field_block",
                profile_transport_kind=transport_kind,
            )
        )
    return tuple(cells)


def _overlays_for_routeable_group(
    group: RouteableInnerGroupPlacement,
    *,
    miner_kind: str,
    extension_kind: str,
) -> list[ReplayOverlayCell]:
    out: list[ReplayOverlayCell] = []
    for x, y in group.miner_cells:
        out.append(ReplayOverlayCell(x=x, y=y, kind=miner_kind, transport=""))
    for x, y in group.extension_cells:
        out.append(ReplayOverlayCell(x=x, y=y, kind=extension_kind, transport=""))
    return out


def _metrics_for_result(result: Layer04InnerFillResult) -> dict[str, object]:
    metrics = result.metrics
    payload: dict[str, object] = {
        "layer": LAYER04_INNER_PATTERN_FILL_PHASE,
        "interior_occupied_cell_count": len(result.interior_occupied_cells),
        "placement_count": len(result.placements),
        "routeable_inner_group_count": len(result.routeable_inner_groups),
    }
    if metrics is not None:
        payload["coverage_ratio"] = metrics.coverage_ratio
        payload["budget_interrupted"] = metrics.budget_interrupted
    if result.skip_reason is not None:
        payload["skip_reason"] = result.skip_reason.value
    return payload


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
        phase=ReplayPhase.PATTERN_GENERATION,
        title=title,
        description=description,
        metrics=metrics,
        transient_overlay_cells=transient_overlay_cells,
        inspector=dict(_L4_INNER_FILL_INSPECTOR),
    )


def build_layer04_inner_pattern_fill_frames(
    result: Layer04InnerFillResult,
    *,
    transport_kind: str = "space_belt",
) -> tuple[ReplaySegmentFrameSpec, ...]:
    overlays = _overlay_cells_for_result(result, transport_kind=transport_kind)
    metrics = _metrics_for_result(result)
    begin = _spec(
        event_type=ReplayEventType.LAYER04_INNER_PATTERN_FILL_BEGIN,
        title="Layer 04 inner pattern fill begin",
        description="Greedy interior field occupancy and routeable inner groups",
        metrics=metrics,
        transient_overlay_cells=overlays,
    )
    complete = _spec(
        event_type=ReplayEventType.LAYER04_INNER_PATTERN_FILL_COMPLETE,
        title="Layer 04 inner pattern fill complete",
        description=(
            f"Occupied {metrics['interior_occupied_cell_count']} interior cell(s); "
            f"{metrics['routeable_inner_group_count']} routeable group(s)"
        ),
        metrics=metrics,
        transient_overlay_cells=overlays,
    )
    return (begin, complete)


def build_persistent_inner_fill_overlay_wire(
    result: Layer04InnerFillResult,
    *,
    transport_kind: str = "space_belt",
) -> list[dict[str, object]]:
    """Committed L4 interior occupancy carried on L5+ runtime frames."""

    from django_apps.asteroid_lab.replay.runtime_frame_finalize import (
        transient_overlay_cells_to_wire,
    )

    if not result.interior_occupied_cells:
        return []
    cells = _overlay_cells_for_result(result, transport_kind=transport_kind)
    wire = transient_overlay_cells_to_wire(cells)
    for row in wire:
        row["overlay_role"] = COMMITTED_INNER_FILL_OVERLAY_ROLE
    return wire


__all__ = [
    "COMMITTED_INNER_FILL_OVERLAY_ROLE",
    "LAYER04_INNER_PATTERN_FILL_PHASE",
    "build_layer04_inner_pattern_fill_frames",
    "build_persistent_inner_fill_overlay_wire",
]
