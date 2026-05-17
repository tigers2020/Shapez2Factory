"""Sequence 8 — typed replay event emission helpers (output-only, sink optional)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from django_apps.shapez_asteroid.optimization.commit_survivability_metrics import (
    commit_survivability_metrics_to_replay_metrics,
)
from django_apps.shapez_asteroid.optimization.dto import (
    CommitSurvivabilityMetrics,
    FitnessBreakdown,
    Genome,
    OptimizationInput,
    RouteReservation,
    ValidationResult,
)
from django_apps.shapez_asteroid.optimization.enums import (
    CommitConflictReason,
    EvolutionConvergenceReason,
    OptimizationReplayEventType,
    TransportKind,
    ValidationSeverity,
)
from django_apps.shapez_asteroid.optimization.optimization_replay import OptimizationReplaySink


def emit_optimization_input_loaded(
    recorder: OptimizationReplaySink | None,
    *,
    title: str = "Optimization input loaded",
    description: str = "",
    candidate_count: int | None = None,
    rejected_candidate_count: int | None = None,
    visible_cells: tuple[object, ...] = (),
    overlay_cells: tuple[object, ...] = (),
    extra_metrics: Mapping[str, object] | None = None,
) -> None:
    if recorder is None:
        return
    m: dict[str, object] = {}
    if candidate_count is not None:
        m["candidate_count"] = candidate_count
    if rejected_candidate_count is not None:
        m["rejected_candidate_count"] = rejected_candidate_count
    if extra_metrics:
        m.update(dict(extra_metrics))
    recorder.record_replay_frame(
        event_type=OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
        title=title,
        description=description,
        visible_cells=visible_cells,
        overlay_cells=overlay_cells,
        metrics=m,
    )


def emit_genome_generated(
    recorder: OptimizationReplaySink | None,
    *,
    title: str,
    description: str = "",
    genome_id: str | None = None,
    generation_index: int | None = None,
    population_size: int | None = None,
    genome_ids: Sequence[str] | None = None,
    candidate_count: int | None = None,
    visible_cells: tuple[object, ...] = (),
    overlay_cells: tuple[object, ...] = (),
    extra_metrics: Mapping[str, object] | None = None,
) -> None:
    if recorder is None:
        return
    m: dict[str, object] = {}
    if genome_id is not None:
        m["genome_id"] = genome_id
    if generation_index is not None:
        m["generation_index"] = generation_index
    if population_size is not None:
        m["population_size"] = population_size
    if genome_ids is not None:
        m["genome_ids"] = tuple(genome_ids)
    if candidate_count is not None:
        m["candidate_count"] = candidate_count
    if extra_metrics:
        m.update(dict(extra_metrics))
    recorder.record_replay_frame(
        event_type=OptimizationReplayEventType.GENOME_GENERATED,
        title=title,
        description=description,
        visible_cells=visible_cells,
        overlay_cells=overlay_cells,
        metrics=m,
    )


def emit_genome_evaluated(
    recorder: OptimizationReplaySink | None,
    *,
    title: str,
    description: str = "",
    genome_id: str,
    generation_index: int,
    fitness_total: float,
    fitness_breakdown: FitnessBreakdown | None = None,
    visible_cells: tuple[object, ...] = (),
    overlay_cells: tuple[object, ...] = (),
    extra_metrics: Mapping[str, object] | None = None,
) -> None:
    if recorder is None:
        return
    m: dict[str, object] = {
        "genome_id": genome_id,
        "generation_index": generation_index,
        "fitness_total": fitness_total,
    }
    if fitness_breakdown is not None:
        m["fitness_breakdown"] = fitness_breakdown
    if extra_metrics:
        m.update(dict(extra_metrics))
    recorder.record_replay_frame(
        event_type=OptimizationReplayEventType.GENOME_EVALUATED,
        title=title,
        description=description,
        visible_cells=visible_cells,
        overlay_cells=overlay_cells,
        metrics=m,
    )


def emit_generation_completed(
    recorder: OptimizationReplaySink | None,
    *,
    title: str,
    description: str = "",
    generation_index: int,
    fitness_total: float,
    population_size: int,
    evaluated_count: int,
    visible_cells: tuple[object, ...] = (),
    overlay_cells: tuple[object, ...] = (),
    extra_metrics: Mapping[str, object] | None = None,
) -> None:
    if recorder is None:
        return
    m: dict[str, object] = {
        "generation_index": generation_index,
        "fitness_total": fitness_total,
        "population_size": population_size,
        "evaluated_count": evaluated_count,
    }
    if extra_metrics:
        m.update(dict(extra_metrics))
    recorder.record_replay_frame(
        event_type=OptimizationReplayEventType.GENERATION_COMPLETED,
        title=title,
        description=description,
        visible_cells=visible_cells,
        overlay_cells=overlay_cells,
        metrics=m,
    )


def emit_best_genome_selected(
    recorder: OptimizationReplaySink | None,
    *,
    title: str = "Best genome selected",
    description: str = "",
    genome: Genome,
    fitness_total: float,
    fitness_breakdown: FitnessBreakdown | None = None,
    selected_candidate_count: int | None = None,
    evolution_convergence_reason: EvolutionConvergenceReason,
    visible_cells: tuple[object, ...] = (),
    overlay_cells: tuple[object, ...] = (),
    extra_metrics: Mapping[str, object] | None = None,
) -> None:
    if recorder is None:
        return
    m: dict[str, object] = {
        "genome_id": genome.genome_id,
        "fitness_total": fitness_total,
        "evolution_convergence_reason": evolution_convergence_reason,
    }
    if fitness_breakdown is not None:
        m["fitness_breakdown"] = fitness_breakdown
    if selected_candidate_count is not None:
        m["selected_candidate_count"] = selected_candidate_count
    if extra_metrics:
        m.update(dict(extra_metrics))
    recorder.record_replay_frame(
        event_type=OptimizationReplayEventType.BEST_GENOME_SELECTED,
        title=title,
        description=description,
        visible_cells=visible_cells,
        overlay_cells=overlay_cells,
        metrics=m,
    )


def emit_route_commit_attempted(
    recorder: OptimizationReplaySink | None,
    *,
    title: str = "Route commit attempted",
    description: str = "",
    candidate_id: str,
    transport_kind: TransportKind,
    visible_cells: tuple[object, ...] = (),
    overlay_cells: tuple[object, ...] = (),
    extra_metrics: Mapping[str, object] | None = None,
) -> None:
    if recorder is None:
        return
    m: dict[str, object] = {"candidate_id": candidate_id, "transport_kind": transport_kind}
    if extra_metrics:
        m.update(dict(extra_metrics))
    recorder.record_replay_frame(
        event_type=OptimizationReplayEventType.ROUTE_COMMIT_ATTEMPTED,
        title=title,
        description=description,
        visible_cells=visible_cells,
        overlay_cells=overlay_cells,
        metrics=m,
    )


def emit_route_committed(
    recorder: OptimizationReplaySink | None,
    *,
    title: str = "Route committed",
    description: str = "",
    candidate_id: str,
    reservation: RouteReservation,
    visible_cells: tuple[object, ...] = (),
    overlay_cells: tuple[object, ...] = (),
    extra_metrics: Mapping[str, object] | None = None,
) -> None:
    if recorder is None:
        return
    m: dict[str, object] = {
        "candidate_id": candidate_id,
        "route_reservation_id": reservation.reservation_id,
        "reservation_state": reservation.reservation_state,
        "route_cost": reservation.cost,
        "reached_goal_kind": reservation.reached_goal.goal_kind,
        "goal_priority": reservation.goal_priority,
        "transport_kind": reservation.transport_kind,
    }
    if extra_metrics:
        m.update(dict(extra_metrics))
    recorder.record_replay_frame(
        event_type=OptimizationReplayEventType.ROUTE_COMMITTED,
        title=title,
        description=description,
        visible_cells=visible_cells,
        overlay_cells=overlay_cells,
        metrics=m,
    )


def emit_route_rolled_back(
    recorder: OptimizationReplaySink | None,
    *,
    title: str = "Route rolled back",
    description: str = "",
    candidate_id: str,
    transport_kind: TransportKind,
    commit_conflict_reason: CommitConflictReason | None = None,
    visible_cells: tuple[object, ...] = (),
    overlay_cells: tuple[object, ...] = (),
    extra_metrics: Mapping[str, object] | None = None,
) -> None:
    if recorder is None:
        return
    m: dict[str, object] = {"candidate_id": candidate_id, "transport_kind": transport_kind}
    if commit_conflict_reason is not None:
        m["commit_conflict_reason"] = commit_conflict_reason
    if extra_metrics:
        m.update(dict(extra_metrics))
    recorder.record_replay_frame(
        event_type=OptimizationReplayEventType.ROUTE_ROLLED_BACK,
        title=title,
        description=description,
        visible_cells=visible_cells,
        overlay_cells=overlay_cells,
        metrics=m,
    )


def emit_commit_survivability_summary(
    recorder: OptimizationReplaySink | None,
    metrics: CommitSurvivabilityMetrics,
    *,
    title: str = "Commit survivability summary",
    description: str = "",
    route_fragility_penalty: float = 0.0,
    shared_corridor_pressure_penalty: float = 0.0,
    visible_cells: tuple[object, ...] = (),
    overlay_cells: tuple[object, ...] = (),
    extra_metrics: Mapping[str, object] | None = None,
) -> None:
    if recorder is None:
        return
    m: dict[str, object] = commit_survivability_metrics_to_replay_metrics(
        metrics,
        route_fragility_penalty=route_fragility_penalty,
        shared_corridor_pressure_penalty=shared_corridor_pressure_penalty,
    )
    if extra_metrics:
        m.update(dict(extra_metrics))
    recorder.record_replay_frame(
        event_type=OptimizationReplayEventType.COMMIT_SURVIVABILITY_SUMMARY,
        title=title,
        description=description,
        visible_cells=visible_cells,
        overlay_cells=overlay_cells,
        metrics=m,
    )


def emit_validation_completed(
    recorder: OptimizationReplaySink | None,
    *,
    title: str = "Validation completed",
    description: str = "",
    result: ValidationResult,
    route_reservation_ids: Sequence[str] | None = None,
    visible_cells: tuple[object, ...] = (),
    overlay_cells: tuple[object, ...] = (),
    extra_metrics: Mapping[str, object] | None = None,
) -> None:
    if recorder is None:
        return
    issues = result.issues
    err = sum(1 for i in issues if i.severity is ValidationSeverity.ERROR)
    warn = sum(1 for i in issues if i.severity is ValidationSeverity.WARNING)
    info = sum(1 for i in issues if i.severity is ValidationSeverity.INFO)
    codes = sorted({i.issue_code for i in issues}, key=lambda c: c.value)
    m: dict[str, object] = {
        "validation_passed": result.passed,
        "validation_issue_count": len(issues),
        "validation_error_count": err,
        "validation_warning_count": warn,
        "validation_info_count": info,
        "issue_codes": tuple(codes),
    }
    if route_reservation_ids is not None:
        m["route_reservation_ids"] = tuple(sorted(route_reservation_ids))
    if extra_metrics:
        m.update(dict(extra_metrics))
    recorder.record_replay_frame(
        event_type=OptimizationReplayEventType.VALIDATION_COMPLETED,
        title=title,
        description=description,
        visible_cells=visible_cells,
        overlay_cells=overlay_cells,
        metrics=m,
    )


def optimization_input_loaded_metrics(inp: OptimizationInput) -> dict[str, object]:
    """Scalar-ish snapshot for replay (deterministic; no RNG)."""

    return {
        "asteroid_cell_count": len(inp.asteroid_cells),
        "mineable_cell_count": len(inp.mineable_cells),
        "rim_cell_count": len(inp.rim_cells),
        "route_goal_count": len(inp.route_goals),
        "existing_transport_cell_count": len(inp.existing_transport_cells),
        "bbox_min_x": inp.bbox.min_x,
        "bbox_max_x": inp.bbox.max_x,
        "bbox_min_y": inp.bbox.min_y,
        "bbox_max_y": inp.bbox.max_y,
    }


__all__ = [
    "emit_best_genome_selected",
    "emit_commit_survivability_summary",
    "emit_generation_completed",
    "emit_genome_evaluated",
    "emit_genome_generated",
    "emit_optimization_input_loaded",
    "emit_route_commit_attempted",
    "emit_route_committed",
    "emit_route_rolled_back",
    "emit_validation_completed",
    "optimization_input_loaded_metrics",
]
