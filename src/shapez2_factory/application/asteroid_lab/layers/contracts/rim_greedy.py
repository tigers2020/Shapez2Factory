"""Integrated rim greedy placement contracts (layer 03 canonical)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy_append import (
    Layer03AppendResult,
    build_empty_layer03_append_result,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

LAYER_03_GREEDY_SOURCE = LAYER_03_RIM_GREEDY_PLACEMENT


class RimGreedyRejectReason(StrEnum):
    ANCHOR_ALREADY_CONSUMED = "ANCHOR_ALREADY_CONSUMED"
    ANCHOR_INVALIDATED = "ANCHOR_INVALIDATED"
    NO_VOID_NORMAL = "NO_VOID_NORMAL"
    FOOTPRINT_OUT_OF_FIELD = "FOOTPRINT_OUT_OF_FIELD"
    EQUIPMENT_COLLISION = "EQUIPMENT_COLLISION"
    PRIORITY_RULE_VIOLATION = "PRIORITY_RULE_VIOLATION"
    M_OUTPUT_BLOCKED = "M_OUTPUT_BLOCKED"
    DPS_UNREACHABLE = "DPS_UNREACHABLE"
    ROUTE_CROSSES_HARD_BLOCKER = "ROUTE_CROSSES_HARD_BLOCKER"
    ORIENTATION_MISMATCH = "ORIENTATION_MISMATCH"


class RimGreedyObservationPhase(StrEnum):
    RIM_GREEDY_BEGIN = "rim_greedy_begin"
    RIM_ANCHOR_PROBE = "rim_anchor_probe"
    RIM_SEED_ATTEMPT_REJECTED = "rim_seed_attempt_rejected"
    RIM_SEED_COMMITTED = "rim_seed_committed"
    RIM_ROUTE_PROBE_SUCCESS = "rim_route_probe_success"
    RIM_ROUTE_PROBE_FAILED = "rim_route_probe_failed"
    RIM_PASS1_COMPLETE = "rim_pass1_complete"
    RIM_PASS2_VALIDATION = "rim_pass2_validation"
    RIM_GREEDY_COMPLETE = "rim_greedy_complete"


@dataclass(frozen=True, slots=True)
class RimGreedyPolicy:
    dps_search_margin: int = 12
    min_rim_anchor_fill_ratio: float = 0.95

    @classmethod
    def default(cls) -> RimGreedyPolicy:
        return cls()


@dataclass(frozen=True, slots=True)
class RimGreedyScoreAtoms:
    miner_count: int
    extension_count: int
    route_length: int
    base_score: float


@dataclass(frozen=True, slots=True)
class CommittedRimSeedPlacement:
    placement_id: str
    variant_id: str
    anchor: Coord
    output_dir: str
    seed_id: str
    miner_cells: frozenset[Coord]
    extension_cells: frozenset[Coord]
    m_output_stub: Coord
    route_probe_path: tuple[Coord, ...]


@dataclass(frozen=True, slots=True)
class RimGreedyReject:
    anchor: Coord
    variant_id: str
    output_dir: str | None
    seed_id: str | None
    reason: RimGreedyRejectReason
    detail: str = ""


@dataclass(frozen=True, slots=True)
class RimGreedyObservationEvent:
    phase: RimGreedyObservationPhase
    variant_id: str
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RimGreedyPass2Report:
    variant_id: str
    score: float | None
    hard_fail: bool
    miner_count: int
    extension_count: int
    total_route_length: int


@dataclass(frozen=True, slots=True)
class RimGreedyMetrics:
    rim_anchor_count: int = 0
    route_feasible_rim_anchor_count: int = 0
    committed_placement_count: int = 0
    rejected_attempt_count: int = 0
    reserved_route_cell_count: int = 0
    winning_variant_id: str = ""
    pass2_score: float | None = None
    layer_skip_reason: str | None = None
    canonical_layer_slug: str = LAYER_03_RIM_GREEDY_PLACEMENT


@dataclass(frozen=True, slots=True)
class IntegratedRimGreedyResult:
    committed_placements: tuple[CommittedRimSeedPlacement, ...]
    rejected_attempts: tuple[RimGreedyReject, ...]
    occupied_equipment_cells: frozenset[Coord]
    reserved_route_cells: frozenset[Coord]
    append_result: Layer03AppendResult
    provisional_overlay: ProvisionalLayoutOverlay
    pass2_report: RimGreedyPass2Report
    winning_variant_id: str
    metrics: RimGreedyMetrics
    observability_events: tuple[RimGreedyObservationEvent, ...]


def build_layer03_reset_observability_events() -> tuple[RimGreedyObservationEvent, ...]:
    """BEGIN/COMPLETE pair for intentional L3 algorithm reset (no placements)."""
    from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
        Layer03SkipReason,
    )

    return _skip_observability_events(
        layer_skip_reason=Layer03SkipReason.ALGORITHM_RESET.value,
        rim_anchor_count=0,
    )


def _skip_observability_events(
    *,
    layer_skip_reason: str,
    rim_anchor_count: int,
) -> tuple[RimGreedyObservationEvent, ...]:
    payload = {
        "layer_skip_reason": layer_skip_reason,
        "rim_anchor_count": rim_anchor_count,
    }
    return (
        RimGreedyObservationEvent(
            phase=RimGreedyObservationPhase.RIM_GREEDY_BEGIN,
            variant_id="",
            payload=payload,
        ),
        RimGreedyObservationEvent(
            phase=RimGreedyObservationPhase.RIM_GREEDY_COMPLETE,
            variant_id="",
            payload=payload,
        ),
    )


def build_empty_integrated_rim_greedy_result(
    *,
    layer_skip_reason: str | None = None,
    rim_anchor_count: int = 0,
    observability_events: tuple[RimGreedyObservationEvent, ...] | None = None,
) -> IntegratedRimGreedyResult:
    overlay = ProvisionalLayoutOverlay(
        occupied_cells=frozenset(),
        extractor_cells=frozenset(),
        extension_cells=frozenset(),
        transport_stub_cells=frozenset(),
        by_cell={},
        source_layer=LAYER_03_GREEDY_SOURCE,
    )
    report = RimGreedyPass2Report(
        variant_id="",
        score=None,
        hard_fail=True,
        miner_count=0,
        extension_count=0,
        total_route_length=0,
    )
    metrics = RimGreedyMetrics(
        rim_anchor_count=rim_anchor_count,
        layer_skip_reason=layer_skip_reason,
    )
    return IntegratedRimGreedyResult(
        committed_placements=(),
        rejected_attempts=(),
        occupied_equipment_cells=frozenset(),
        reserved_route_cells=frozenset(),
        append_result=build_empty_layer03_append_result(),
        provisional_overlay=overlay,
        pass2_report=report,
        winning_variant_id="",
        metrics=metrics,
        observability_events=observability_events
        or (
            _skip_observability_events(
                layer_skip_reason=layer_skip_reason or "unknown",
                rim_anchor_count=rim_anchor_count,
            )
            if layer_skip_reason is not None
            else ()
        ),
    )


__all__ = [
    "CommittedRimSeedPlacement",
    "IntegratedRimGreedyResult",
    "Layer03AppendResult",
    "LAYER_03_GREEDY_SOURCE",
    "RimGreedyMetrics",
    "RimGreedyObservationEvent",
    "RimGreedyObservationPhase",
    "RimGreedyPass2Report",
    "RimGreedyPolicy",
    "RimGreedyReject",
    "RimGreedyRejectReason",
    "RimGreedyScoreAtoms",
    "_skip_observability_events",
    "build_empty_integrated_rim_greedy_result",
    "build_layer03_reset_observability_events",
]
