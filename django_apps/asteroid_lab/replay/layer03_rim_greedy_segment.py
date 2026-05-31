"""Layer 03 rim greedy placement replay segment (transient overlay specs only)."""

from __future__ import annotations

from typing import Literal

from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_LAYER03_RIM_GREEDY_BEGIN,
    EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE,
    EVENT_TYPE_LAYER03_RIM_GREEDY_PASS1_COMPLETE,
    EVENT_TYPE_LAYER03_RIM_GREEDY_SEED_COMMITTED,
    assert_registered_event_type,
)
from django_apps.asteroid_lab.replay.layer03_overlay_cells import (
    OVERLAY_KIND_CANDIDATE_MINER,
    OVERLAY_KIND_CANDIDATE_ROUTE_PATH,
    OVERLAY_KIND_CANDIDATE_TRANSPORT_STUB,
)
from django_apps.asteroid_lab.replay.pattern_bundle_highlight import (
    METRICS_KEY,
    build_pattern_bundle_highlights_wire,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.replay_limits import LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS
from django_apps.asteroid_lab.replay.segment_frame_spec import ReplaySegmentFrameSpec
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayOverlayCell
from django_apps.asteroid_lab.snapshots.equipment_bundles import ports_compatible
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
    IntegratedRimGreedyResult,
    RimGreedyObservationEvent,
    RimGreedyObservationPhase,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy_append import (
    AppendCellKind,
    AppendedPlacementCell,
    Layer03AppendResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    TransportKind,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

LAYER03_GREEDY_PHASE = LAYER_03_RIM_GREEDY_PLACEMENT

_PHASE_TO_EVENT: dict[RimGreedyObservationPhase, str] = {
    RimGreedyObservationPhase.RIM_GREEDY_BEGIN: EVENT_TYPE_LAYER03_RIM_GREEDY_BEGIN,
    RimGreedyObservationPhase.RIM_PASS1_COMPLETE: EVENT_TYPE_LAYER03_RIM_GREEDY_PASS1_COMPLETE,
    RimGreedyObservationPhase.RIM_SEED_COMMITTED: EVENT_TYPE_LAYER03_RIM_GREEDY_SEED_COMMITTED,
    RimGreedyObservationPhase.RIM_GREEDY_COMPLETE: EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE,
}

_GREEDY_INSPECTOR = {
    "lab_phase": "rim_greedy_placement",
    "lab_phase_step": LAYER03_GREEDY_PHASE,
}

_CARDINAL_DIR_DELTA: dict[str, tuple[int, int]] = {
    "N": (0, -1),
    "E": (1, 0),
    "S": (0, 1),
    "W": (-1, 0),
}
_MAP_FACING_DIR_TO_PORT: dict[str, str] = {
    "N": "n",
    "E": "e",
    "S": "s",
    "W": "w",
}
_OUTPUT_TO_ROTATION: dict[str, int] = {"E": 0, "S": 1, "W": 2, "N": 3}
_CARDINAL_DIR_ALIASES: dict[str, str] = {
    "n": "N",
    "e": "E",
    "s": "S",
    "w": "W",
    "N": "N",
    "E": "E",
    "S": "S",
    "W": "W",
}


def _canonical_cardinal_dir(output_dir: str) -> str:
    """Normalize ``Direction`` wire (``n``/``e``/``s``/``w``) to uppercase grid keys."""

    key = output_dir.strip()
    canon = _CARDINAL_DIR_ALIASES.get(key) or _CARDINAL_DIR_ALIASES.get(key.lower())
    if canon is None:
        msg = f"unsupported output_dir={output_dir!r}"
        raise ValueError(msg)
    return canon


def _event_type_for_phase(phase: RimGreedyObservationPhase) -> ReplayEventType:
    wire = _PHASE_TO_EVENT[phase]
    assert_registered_event_type(wire)
    return ReplayEventType(wire)


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
        inspector={**_GREEDY_INSPECTOR, "lab_event_type": event_type.value},
    )


def _transport_wire() -> str:
    return TransportKind.SHAPE_BELT.value


def _placement_output_rotation(output_dir: str) -> int:
    return _OUTPUT_TO_ROTATION[_canonical_cardinal_dir(output_dir)]


def _direction_child_to_parent(child: Coord, parent: Coord) -> str | None:
    dx = parent[0] - child[0]
    dy = parent[1] - child[1]
    for name, (ddx, ddy) in _CARDINAL_DIR_DELTA.items():
        if dx == ddx and dy == ddy:
            return _MAP_FACING_DIR_TO_PORT[name]
    return None


def _placement_extension_rotation(
    *,
    miner_coord: Coord,
    extension_coord: Coord,
    miner_rotation: int,
    extension_kind: str = "shape_miner_extension",
    miner_kind: str = "shape_miner",
) -> int:
    dir_child_to_parent = _direction_child_to_parent(extension_coord, miner_coord)
    if dir_child_to_parent is None:
        msg = "extension and miner are not 4-neighbors on the map grid"
        raise ValueError(msg)
    for rotation in range(4):
        if ports_compatible(
            extension_kind,
            rotation,
            miner_kind,
            miner_rotation,
            dir_child_to_parent,
        ):
            return rotation
    msg = "no extension rotation links extension to miner"
    raise ValueError(msg)


_APPEND_TO_REPLAY_KIND_OBSERVATION: dict[AppendCellKind, str] = {
    AppendCellKind.MINER: OVERLAY_KIND_CANDIDATE_MINER,
    AppendCellKind.EXTENSION: OVERLAY_KIND_CANDIDATE_MINER,
    AppendCellKind.OUTPUT_STUB: OVERLAY_KIND_CANDIDATE_TRANSPORT_STUB,
    AppendCellKind.ROUTE_RESERVED: OVERLAY_KIND_CANDIDATE_ROUTE_PATH,
}

_APPEND_TO_REPLAY_KIND_COMMITTED: dict[AppendCellKind, str] = {
    AppendCellKind.MINER: "shape_miner",
    AppendCellKind.EXTENSION: "shape_miner_extension",
    AppendCellKind.OUTPUT_STUB: OVERLAY_KIND_CANDIDATE_TRANSPORT_STUB,
    AppendCellKind.ROUTE_RESERVED: OVERLAY_KIND_CANDIDATE_ROUTE_PATH,
}

GreedyReplayEquipmentWire = Literal["observation", "committed"]


def _parent_coord_for_extension(
    placement: CommittedRimSeedPlacement,
    extension_coord: Coord,
) -> Coord:
    """Chain parent (one step toward the miner) for a straight inward extension.

    Extensions extend inward as ``anchor - k * delta(output_dir)``, so the parent of
    any extension is ``extension + delta(output_dir)``: the miner for the first
    extension, or the preceding extension for deeper links. This keeps the parent a
    4-neighbor so ``placement_extension_rotation`` resolves for m3e_01 chains.
    """
    dx, dy = _CARDINAL_DIR_DELTA[_canonical_cardinal_dir(placement.output_dir)]
    return (extension_coord[0] + dx, extension_coord[1] + dy)


def _rotation_for_append_cell(
    cell: AppendedPlacementCell,
    placement: CommittedRimSeedPlacement | None,
) -> int:
    if placement is None:
        return 0
    miner_rotation = _placement_output_rotation(placement.output_dir)
    if cell.kind is AppendCellKind.MINER:
        return miner_rotation
    if cell.kind is AppendCellKind.EXTENSION:
        parent_coord = _parent_coord_for_extension(placement, cell.coord)
        return _placement_extension_rotation(
            miner_coord=parent_coord,
            extension_coord=cell.coord,
            miner_rotation=miner_rotation,
        )
    return 0


def _replay_overlay_from_append(
    append_result: Layer03AppendResult,
    *,
    placements: tuple[CommittedRimSeedPlacement, ...] = (),
    placement_ids: frozenset[str] | None = None,
    equipment_wire: GreedyReplayEquipmentWire = "observation",
) -> tuple[ReplayOverlayCell, ...]:
    """Lab replay wire from append cells (same coord collapse as provisional overlay)."""

    transport = _transport_wire()
    kind_map = (
        _APPEND_TO_REPLAY_KIND_COMMITTED
        if equipment_wire == "committed"
        else _APPEND_TO_REPLAY_KIND_OBSERVATION
    )
    placement_by_id = {p.placement_id: p for p in placements}
    cells = append_result.cells
    if placement_ids is not None:
        cells = tuple(c for c in cells if c.placement_id in placement_ids)
    overlay: list[ReplayOverlayCell] = []
    for cell in cells:
        placement = placement_by_id.get(cell.placement_id)
        rotation = _rotation_for_append_cell(cell, placement)
        overlay.append(
            ReplayOverlayCell(
                x=cell.coord[0],
                y=cell.coord[1],
                kind=kind_map[cell.kind],
                transport=transport,
                rotation=rotation,
            )
        )
    return tuple(overlay)


def _transient_overlay_for_greedy_result(
    result: IntegratedRimGreedyResult,
    *,
    placements: tuple[CommittedRimSeedPlacement, ...],
    equipment_wire: GreedyReplayEquipmentWire = "observation",
) -> tuple[ReplayOverlayCell, ...]:
    if result.append_result.cells:
        placement_ids = frozenset(p.placement_id for p in placements)
        return _replay_overlay_from_append(
            result.append_result,
            placements=result.committed_placements,
            placement_ids=placement_ids,
            equipment_wire=equipment_wire,
        )
    return _combined_overlay_for_placements(placements)


def _combined_overlay_for_placements(
    placements: tuple[CommittedRimSeedPlacement, ...],
) -> tuple[ReplayOverlayCell, ...]:
    combined: list[ReplayOverlayCell] = []
    for placement in placements:
        combined.extend(_overlay_for_committed(placement))
    return tuple(combined)


def _overlay_for_committed(
    placement: CommittedRimSeedPlacement,
) -> tuple[ReplayOverlayCell, ...]:
    transport = _transport_wire()
    overlay: list[ReplayOverlayCell] = []
    equipment = sorted(placement.miner_cells | placement.extension_cells)
    for x, y in equipment:
        overlay.append(
            ReplayOverlayCell(
                x=x,
                y=y,
                kind=OVERLAY_KIND_CANDIDATE_MINER,
                transport=transport,
            )
        )
    for x, y in sorted({placement.m_output_stub}):
        overlay.append(
            ReplayOverlayCell(
                x=x,
                y=y,
                kind=OVERLAY_KIND_CANDIDATE_TRANSPORT_STUB,
                transport=transport,
            )
        )
    for x, y in placement.route_probe_path:
        overlay.append(
            ReplayOverlayCell(
                x=x,
                y=y,
                kind=OVERLAY_KIND_CANDIDATE_ROUTE_PATH,
                transport=transport,
            )
        )
    return tuple(overlay)


def _pattern_highlights_for_placements(
    placements: tuple[CommittedRimSeedPlacement, ...],
) -> dict[str, object]:
    entries: list[tuple[str, frozenset[Coord], str | None]] = []
    for placement in placements:
        footprint = placement.miner_cells | placement.extension_cells
        entries.append((placement.placement_id, footprint, placement.seed_id))
    return build_pattern_bundle_highlights_wire(entries)


def _chunk_placements(
    placements: tuple[CommittedRimSeedPlacement, ...],
    *,
    max_windows: int,
) -> list[tuple[CommittedRimSeedPlacement, ...]]:
    if not placements or max_windows <= 0:
        return []
    count = len(placements)
    window_count = min(max_windows, count)
    chunk_size = max(1, (count + window_count - 1) // window_count)
    chunks: list[tuple[CommittedRimSeedPlacement, ...]] = []
    index = 0
    while index < count:
        chunks.append(placements[index : index + chunk_size])
        index += chunk_size
    return chunks


def build_layer03_rim_greedy_runtime_segment_specs(
    result: IntegratedRimGreedyResult,
) -> tuple[ReplaySegmentFrameSpec, ...]:
    """Runtime greedy replay; transient overlays follow ``result.append_result`` when set."""
    """Winning-variant greedy replay with overlays (Lab map tint parity with legacy L3 pool)."""
    placements = result.committed_placements
    metrics = result.metrics
    variant_id = result.winning_variant_id or "—"

    begin = _spec(
        event_type=ReplayEventType.LAYER03_RIM_GREEDY_BEGIN,
        title="Layer 03 rim greedy begin",
        description=f"variant winner={variant_id}",
        metrics={
            "layer": LAYER03_GREEDY_PHASE,
            "phase": RimGreedyObservationPhase.RIM_GREEDY_BEGIN.value,
            "variant_id": variant_id,
            "rim_anchor_count": metrics.rim_anchor_count,
        },
    )

    summary_metrics: dict[str, object] = {
        "layer": LAYER03_GREEDY_PHASE,
        "phase": "rim_greedy_summary",
        "variant_id": variant_id,
        "committed_placement_count": metrics.committed_placement_count,
        "rejected_attempt_count": metrics.rejected_attempt_count,
        "winning_variant_id": variant_id,
        "pass2_score": metrics.pass2_score,
    }
    if placements:
        summary_metrics[METRICS_KEY] = _pattern_highlights_for_placements(placements)

    summary = _spec(
        event_type=ReplayEventType.LAYER03_RIM_GREEDY_SUMMARY,
        title="Layer 03 rim greedy summary",
        description=(
            f"Committed {metrics.committed_placement_count} · "
            f"rejected {metrics.rejected_attempt_count} · variant {variant_id}"
        ),
        metrics=summary_metrics,
    )

    preview_frames: list[ReplaySegmentFrameSpec] = []
    chunks = _chunk_placements(
        placements,
        max_windows=LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS,
    )
    logical_count = len(chunks)
    for window_index, chunk in enumerate(chunks, start=1):
        start = sum(len(c) for c in chunks[: window_index - 1]) + 1
        end = start + len(chunk) - 1
        preview_frames.append(
            _spec(
                event_type=ReplayEventType.LAYER03_RIM_GREEDY_SEED_COMMITTED,
                title=(f"Layer 03 rim greedy · window {window_index} / {logical_count}"),
                description=f"Placements {start}–{end} / {len(placements)}",
                metrics={
                    "layer": LAYER03_GREEDY_PHASE,
                    "phase": RimGreedyObservationPhase.RIM_SEED_COMMITTED.value,
                    "variant_id": variant_id,
                    "window_index": window_index,
                    "logical_window_count": logical_count,
                    "placement_start_index": start,
                    "placement_end_index": end,
                    "committed_placement_count": len(placements),
                },
                transient_overlay_cells=_transient_overlay_for_greedy_result(
                    result,
                    placements=chunk,
                ),
            )
        )

    complete_metrics: dict[str, object] = {
        "layer": LAYER03_GREEDY_PHASE,
        "phase": RimGreedyObservationPhase.RIM_GREEDY_COMPLETE.value,
        "variant_id": variant_id,
        "winning_variant_id": variant_id,
        "pass2_score": metrics.pass2_score,
        "layer_skip_reason": metrics.layer_skip_reason,
        "committed_placement_count": metrics.committed_placement_count,
        "rejected_attempt_count": metrics.rejected_attempt_count,
    }
    complete_highlights = _pattern_highlights_for_placements(placements)
    if complete_highlights:
        complete_metrics[METRICS_KEY] = complete_highlights

    complete = _spec(
        event_type=ReplayEventType.LAYER03_RIM_GREEDY_COMPLETE,
        title="Layer 03 rim greedy complete",
        description=f"Pass2 score={metrics.pass2_score}",
        metrics=complete_metrics,
        transient_overlay_cells=_transient_overlay_for_greedy_result(
            result,
            placements=placements,
            equipment_wire="committed",
        ),
    )

    return (begin, summary, *preview_frames, complete)


def build_layer03_rim_greedy_segment_specs(
    events: tuple[RimGreedyObservationEvent, ...],
) -> tuple[ReplaySegmentFrameSpec, ...]:
    """Legacy event-only projector (metrics frames); prefer runtime builder with overlays."""
    specs: list[ReplaySegmentFrameSpec] = []
    for event in events:
        if event.phase not in _PHASE_TO_EVENT:
            continue
        event_type = _event_type_for_phase(event.phase)
        specs.append(
            ReplaySegmentFrameSpec(
                event_type=event_type,
                phase=ReplayPhase.CANDIDATE_GENERATION,
                title=f"Rim greedy: {event.phase.value}",
                description=f"variant={event.variant_id}",
                metrics={
                    "layer": LAYER03_GREEDY_PHASE,
                    "phase": event.phase.value,
                    "variant_id": event.variant_id,
                    **event.payload,
                },
                inspector={
                    **_GREEDY_INSPECTOR,
                    "lab_event_type": event_type.value,
                },
            )
        )
    return tuple(specs)


__all__ = [
    "build_layer03_rim_greedy_runtime_segment_specs",
    "build_layer03_rim_greedy_segment_specs",
]
