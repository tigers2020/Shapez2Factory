"""Solver runtime replay recorder: A→M pipeline steps → ReplayTimelineFrame (output-only).

Records optimization pipeline events as ReplayTimelineFrame objects. The resulting
frames are a presentation-only artifact and must never be fed back into the solver.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django_apps.asteroid_lab.optimization.candidate_dtos import (
    CandidateGenerationResult,
    GeneCandidate,
    RejectedGeneCandidate,
)
from django_apps.asteroid_lab.optimization.candidate_selector import SelectedCandidatePlan
from django_apps.asteroid_lab.optimization.capacity_planner import CapacityPlan
from django_apps.asteroid_lab.optimization.commit_best_candidates import IncrementalCommitResult
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    ValidationResult,
)
from django_apps.asteroid_lab.optimization.loaded_snapshot import LoadedReconstructionSnapshot
from django_apps.asteroid_lab.optimization.materialization_dtos import RouteMaterializationResult
from django_apps.asteroid_lab.optimization.route_goal_planner import PlannedRouteGoals
from django_apps.asteroid_lab.replay.projection_context import (
    ReplayProjectionContext,
    lab_xy_from_server_xy,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.replay_limits import MAX_SOLVER_RUNTIME_REPLAY_CELLS_PER_FRAME
from django_apps.asteroid_lab.replay.replay_recording_cells import (
    bbox_from_replay_cells,
    candidate_occupied_to_overlay_cells,
    goal_annotations,
    materialized_cells_to_cell_delta,
    probe_path_to_overlay_cells,
    visible_cells_from_loaded_snapshot,
)
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayAnnotation,
    ReplayMapView,
    ReplayTimelineFrame,
)


class SolverRuntimeReplayRecorder:
    """Accumulates solver runtime events as ReplayTimelineFrame objects (output-only).

    Created by the entry layer before pipeline invocation. After the pipeline
    returns, call ``build_frames()`` to retrieve the recorded frames for persist.
    The recorder must never be used as solver algorithm input.
    """

    def __init__(
        self,
        loaded: LoadedReconstructionSnapshot,
        server_xy_params: tuple[int, int],
    ) -> None:
        self._loaded = loaded
        self._ctx = ReplayProjectionContext(server_xy_params=server_xy_params)
        self._frames: list[ReplayTimelineFrame] = []
        self._base_cells_cache: tuple | None = None

    @property
    def _base_cells(self) -> tuple:
        if self._base_cells_cache is None:
            self._base_cells_cache = visible_cells_from_loaded_snapshot(self._loaded, self._ctx)
        return self._base_cells_cache

    def _append(
        self,
        *,
        phase: ReplayPhase,
        event_type: ReplayEventType,
        title: str,
        description: str,
        map_view: ReplayMapView,
        inspector: dict[str, Any] | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        self._frames.append(
            ReplayTimelineFrame(
                frame_index=len(self._frames),
                phase=phase,
                event_type=event_type,
                title=title,
                description=description,
                map_view=map_view,
                inspector=inspector or {},
                metrics=metrics or {},
            )
        )

    def record_optimization_input_loaded(self, inp: OptimizationInput) -> None:
        cells = self._base_cells
        source_count = len(self._loaded.cells)
        recorded_count = len(cells)
        cap = MAX_SOLVER_RUNTIME_REPLAY_CELLS_PER_FRAME
        map_view = ReplayMapView(bbox=bbox_from_replay_cells(cells), full_cells=cells)
        self._append(
            phase=ReplayPhase.OPTIMIZATION_INPUT,
            event_type=ReplayEventType.OPTIMIZATION_INPUT_LOADED,
            title="Optimization Input Loaded",
            description=(
                f"mineable: {len(inp.mineable_cells)}, "
                f"rim: {len(inp.rim_cells)}, "
                f"goals: {len(inp.route_goals)}"
            ),
            map_view=map_view,
            inspector={
                "mineable_cell_count": len(inp.mineable_cells),
                "rim_cell_count": len(inp.rim_cells),
                "route_goal_count": len(inp.route_goals),
                "full_cell_count": recorded_count,
                "source_cell_count": source_count,
                "recorded_cell_cap": cap,
                "truncated": source_count > recorded_count,
                "dropped_cell_count": max(0, source_count - recorded_count),
            },
        )

    def record_capacity_plan_created(self, capacity: CapacityPlan) -> None:
        cells = self._base_cells
        map_view = ReplayMapView(bbox=bbox_from_replay_cells(cells), full_cells=cells)
        self._append(
            phase=ReplayPhase.OPTIMIZATION_INPUT,
            event_type=ReplayEventType.CAPACITY_PLAN_CREATED,
            title="Capacity Plan Created",
            description=(
                f"shape goals: {capacity.shape_goal_count}, "
                f"fluid goals: {capacity.fluid_goal_count}"
            ),
            map_view=map_view,
            inspector={
                "shape_goal_count": capacity.shape_goal_count,
                "fluid_goal_count": capacity.fluid_goal_count,
                "mineable_cell_count": capacity.mineable_cell_count,
            },
        )

    def record_route_goals_generated(self, planned: PlannedRouteGoals) -> None:
        cells = self._base_cells
        annotations = goal_annotations(planned.goals, self._ctx)
        map_view = ReplayMapView(
            bbox=bbox_from_replay_cells(cells),
            full_cells=cells,
            annotations=annotations,
        )
        self._append(
            phase=ReplayPhase.OPTIMIZATION_INPUT,
            event_type=ReplayEventType.ROUTE_GOAL_GENERATED,
            title="Route Goals Generated",
            description=f"{len(planned.goals)} route goals planned",
            map_view=map_view,
            inspector={"route_goal_count": len(planned.goals)},
        )

    def record_candidate_pool_completed(self, pool: CandidateGenerationResult) -> None:
        cells = self._base_cells
        map_view = ReplayMapView(bbox=bbox_from_replay_cells(cells), full_cells=cells)
        self._append(
            phase=ReplayPhase.CANDIDATE_GENERATION,
            event_type=ReplayEventType.CANDIDATE_POOL_COMPLETED,
            title="Candidate Pool Completed",
            description=(
                f"{len(pool.normal_candidates)} normal, "
                f"{len(pool.rejected_candidates)} rejected"
            ),
            map_view=map_view,
            inspector={
                "normal_candidate_count": len(pool.normal_candidates),
                "rejected_candidate_count": len(pool.rejected_candidates),
            },
        )

    def record_candidate_selection_completed(self, plan: SelectedCandidatePlan) -> None:
        cells = self._base_cells
        map_view = ReplayMapView(bbox=bbox_from_replay_cells(cells), full_cells=cells)
        self._append(
            phase=ReplayPhase.CANDIDATE_GENERATION,
            event_type=ReplayEventType.CANDIDATE_SELECTION_COMPLETED,
            title="Candidate Selection Completed",
            description=f"{len(plan.ordered_candidate_ids)} candidates selected for commit",
            map_view=map_view,
            inspector={"selected_count": len(plan.ordered_candidate_ids)},
        )

    def record_candidate_pool_details(
        self,
        pool: CandidateGenerationResult,
        *,
        max_per_type: int = 8,
    ) -> None:
        """Emit per-candidate generated/rejected and route probe frames (output-only)."""

        cells = self._base_cells
        for candidate in pool.normal_candidates[:max_per_type]:
            occupied_overlay = candidate_occupied_to_overlay_cells(candidate, self._ctx)
            map_view = ReplayMapView(
                bbox=bbox_from_replay_cells(cells, overlay_cells=occupied_overlay),
                full_cells=cells,
                overlay_cells=occupied_overlay,
            )
            probe = candidate.route_probe_result
            self._append(
                phase=ReplayPhase.CANDIDATE_GENERATION,
                event_type=ReplayEventType.CANDIDATE_GENERATED,
                title="Candidate Generated",
                description=candidate.candidate_id,
                map_view=map_view,
                inspector={
                    "candidate_id": candidate.candidate_id,
                    "transport_kind": candidate.transport_kind.value,
                    "base_score": candidate.base_score,
                },
                metrics={
                    "candidate_id": candidate.candidate_id,
                    "transport_kind": candidate.transport_kind.value,
                    "base_score": candidate.base_score,
                    "route_cost": probe.cost,
                },
            )
            path_overlay = probe_path_to_overlay_cells(probe.path, self._ctx)
            probe_map = ReplayMapView(
                bbox=bbox_from_replay_cells(cells, overlay_cells=path_overlay),
                full_cells=cells,
                overlay_cells=path_overlay,
            )
            reached = probe.reached_goal
            self._append(
                phase=ReplayPhase.ROUTE_PROBE,
                event_type=ReplayEventType.ROUTE_PROBE_SUCCEEDED,
                title="Route Probe Succeeded",
                description=candidate.candidate_id,
                map_view=probe_map,
                inspector={
                    "candidate_id": candidate.candidate_id,
                    "reached_goal_kind": (
                        reached.goal_kind.value if reached is not None else None
                    ),
                    "goal_priority": probe.goal_priority,
                },
                metrics={
                    "candidate_id": candidate.candidate_id,
                    "route_cost": probe.cost,
                    "expanded_nodes": probe.expanded_nodes,
                    "goal_priority": probe.goal_priority,
                },
            )

        for rejected in pool.rejected_candidates[:max_per_type]:
            self._record_rejected_candidate_detail(rejected, cells)

    def _record_rejected_candidate_detail(
        self,
        rejected: RejectedGeneCandidate,
        cells: tuple,
    ) -> None:
        annotations: list[ReplayAnnotation] = []
        if rejected.extractor is not None:
            sx, sy = rejected.extractor
            x, y = lab_xy_from_server_xy(sx, sy, server_xy_params=self._ctx.server_xy_params)
            annotations.append(
                ReplayAnnotation(x=x, y=y, label=rejected.rejection_reason.value)
            )
        map_view = ReplayMapView(
            bbox=bbox_from_replay_cells(cells),
            full_cells=cells,
            annotations=tuple(annotations),
        )
        self._append(
            phase=ReplayPhase.CANDIDATE_GENERATION,
            event_type=ReplayEventType.CANDIDATE_REJECTED,
            title="Candidate Rejected",
            description=rejected.rejection_reason.value,
            map_view=map_view,
            inspector={
                "attempted_gene_id": rejected.attempted_gene_id,
                "rejection_reason": rejected.rejection_reason.value,
            },
            metrics={"rejection_reason": rejected.rejection_reason.value},
        )
        probe = rejected.route_probe_result
        if probe is None:
            return
        path_overlay = probe_path_to_overlay_cells(probe.path, self._ctx)
        probe_map = ReplayMapView(
            bbox=bbox_from_replay_cells(cells, overlay_cells=path_overlay),
            full_cells=cells,
            overlay_cells=path_overlay,
        )
        failure = probe.failure_reason.value if probe.failure_reason else None
        self._append(
            phase=ReplayPhase.ROUTE_PROBE,
            event_type=ReplayEventType.ROUTE_PROBE_FAILED,
            title="Route Probe Failed",
            description=rejected.rejection_reason.value,
            map_view=probe_map,
            inspector={
                "attempted_gene_id": rejected.attempted_gene_id,
                "failure_reason": failure,
            },
            metrics={
                "failure_reason": failure,
                "expanded_nodes": probe.expanded_nodes,
            },
        )

    def record_genome_scaffold(
        self,
        plan: SelectedCandidatePlan,
        *,
        pool: CandidateGenerationResult | None = None,
    ) -> None:
        """Emit GA-cycle scaffold frames for greedy selection (output-only)."""

        cells = self._base_cells
        evaluated_count = (
            len(pool.normal_candidates) + len(pool.rejected_candidates) if pool is not None else 0
        )
        selected_count = len(plan.ordered_candidate_ids)
        map_view = ReplayMapView(bbox=bbox_from_replay_cells(cells), full_cells=cells)
        self._append(
            phase=ReplayPhase.GENOME_FITNESS,
            event_type=ReplayEventType.GENOME_EVALUATED,
            title="Genome Evaluated",
            description=f"evaluated={evaluated_count}, selected={selected_count}",
            map_view=map_view,
            inspector={
                "evaluated_count": evaluated_count,
                "selected_count": selected_count,
            },
            metrics={
                "fitness_total": float(selected_count),
                "selected_candidate_count": selected_count,
            },
        )
        self._append(
            phase=ReplayPhase.EVOLUTION,
            event_type=ReplayEventType.BEST_GENOME_SELECTED,
            title="Best Genome Selected",
            description=f"{selected_count} candidates",
            map_view=map_view,
            inspector={"best_candidate_ids": list(plan.ordered_candidate_ids)},
            metrics={
                "best_fitness": float(selected_count),
                "generation_count": 1,
            },
        )
        self._append(
            phase=ReplayPhase.EVOLUTION,
            event_type=ReplayEventType.GENERATION_COMPLETED,
            title="Generation Completed",
            description="generation=1 (greedy scaffold)",
            map_view=map_view,
            inspector={"generation": 1},
            metrics={"generation": 1, "fitness": float(selected_count)},
        )

    def record_commit_details(
        self,
        plan: SelectedCandidatePlan,
        candidates_by_id: Mapping[str, GeneCandidate],
        commit: IncrementalCommitResult,
        *,
        max_candidates: int = 8,
    ) -> None:
        """Emit per-candidate commit attempted / committed / rolled-back frames."""

        cells = self._base_cells
        confirmed_by_id = {c.candidate_id: c for c in commit.confirmed}
        skipped_set = frozenset(commit.skipped_candidate_ids)

        for cid in plan.ordered_candidate_ids[:max_candidates]:
            candidate = candidates_by_id.get(cid)
            confirmed = confirmed_by_id.get(cid)
            path_overlay: tuple = ()
            if candidate is not None and candidate.route_probe_result.path:
                path_overlay = probe_path_to_overlay_cells(
                    candidate.route_probe_result.path, self._ctx
                )
            map_view = ReplayMapView(
                bbox=bbox_from_replay_cells(cells, overlay_cells=path_overlay),
                full_cells=cells,
                overlay_cells=path_overlay,
            )
            reservation_id = confirmed.reservation.reservation_id if confirmed else None
            self._append(
                phase=ReplayPhase.INCREMENTAL_COMMIT,
                event_type=ReplayEventType.ROUTE_COMMIT_ATTEMPTED,
                title="Route Commit Attempted",
                description=cid,
                map_view=map_view,
                inspector={
                    "candidate_id": cid,
                    "reservation_id": reservation_id,
                },
                metrics={"candidate_id": cid, "reservation_id": reservation_id},
            )
            if confirmed is not None:
                res = confirmed.reservation
                self._append(
                    phase=ReplayPhase.INCREMENTAL_COMMIT,
                    event_type=ReplayEventType.ROUTE_COMMITTED,
                    title="Route Committed",
                    description=cid,
                    map_view=map_view,
                    inspector={
                        "candidate_id": cid,
                        "reservation_id": res.reservation_id,
                        "reservation_state": res.reservation_state.value,
                    },
                    metrics={
                        "candidate_id": cid,
                        "reservation_id": res.reservation_id,
                        "reservation_state": res.reservation_state.value,
                        "reserved_cells_count": len(res.reserved_cells),
                    },
                )
            elif cid in skipped_set:
                self._append(
                    phase=ReplayPhase.ROLLBACK,
                    event_type=ReplayEventType.ROUTE_ROLLED_BACK,
                    title="Route Rolled Back",
                    description=cid,
                    map_view=map_view,
                    inspector={"candidate_id": cid},
                    metrics={"candidate_id": cid},
                )

    def record_route_committed(self, commit: IncrementalCommitResult) -> None:
        cells = self._base_cells
        map_view = ReplayMapView(bbox=bbox_from_replay_cells(cells), full_cells=cells)
        self._append(
            phase=ReplayPhase.INCREMENTAL_COMMIT,
            event_type=ReplayEventType.ROUTE_COMMITTED,
            title="Routes Committed",
            description=(
                f"{len(commit.confirmed)} confirmed, "
                f"{len(commit.skipped_candidate_ids)} skipped"
            ),
            map_view=map_view,
            inspector={
                "confirmed_count": len(commit.confirmed),
                "skipped_count": len(commit.skipped_candidate_ids),
            },
        )

    def record_route_materialized(self, materialization: RouteMaterializationResult) -> None:
        cells = self._base_cells
        cell_delta = (
            materialized_cells_to_cell_delta(materialization.layout, self._ctx)
            if materialization.layout is not None
            else ()
        )
        map_view = ReplayMapView(
            bbox=bbox_from_replay_cells(cells, cell_delta=cell_delta),
            full_cells=cells,
            cell_delta=cell_delta,
        )
        failure = materialization.failure_reason.value if materialization.failure_reason else None
        mat_count = len(materialization.layout.cells) if materialization.layout else 0
        self._append(
            phase=ReplayPhase.INCREMENTAL_COMMIT,
            event_type=ReplayEventType.ROUTE_MATERIALIZED,
            title="Route Network Materialized",
            description=f"{mat_count} transport cells",
            map_view=map_view,
            inspector={
                "materialized_cell_count": mat_count,
                "failure_reason": failure,
            },
        )

    def record_validation_completed(self, validation: ValidationResult) -> None:
        cells = self._base_cells
        annotations: list[ReplayAnnotation] = []
        for issue in validation.issues:
            if issue.coord is not None:
                sx, sy = issue.coord
                x, y = lab_xy_from_server_xy(sx, sy, server_xy_params=self._ctx.server_xy_params)
                annotations.append(ReplayAnnotation(x=x, y=y, label=issue.issue_code.value))
        map_view = ReplayMapView(
            bbox=bbox_from_replay_cells(cells),
            full_cells=cells,
            annotations=tuple(annotations),
        )
        event_type = (
            ReplayEventType.VALIDATION_COMPLETED
            if validation.passed
            else ReplayEventType.VALIDATION_FAILED
        )
        self._append(
            phase=ReplayPhase.VALIDATION,
            event_type=event_type,
            title="Validation Completed" if validation.passed else "Validation Failed",
            description=f"passed={validation.passed}, issues={len(validation.issues)}",
            map_view=map_view,
            inspector={
                "passed": validation.passed,
                "issue_count": len(validation.issues),
            },
        )

    def record_result_layout(
        self,
        *,
        commit: IncrementalCommitResult,
        materialization: RouteMaterializationResult,
        validation: ValidationResult,
        solver_summary: dict[str, Any],
    ) -> None:
        """Emit the final result.layout keyframe (always the last recorder frame)."""
        cells = self._base_cells
        cell_delta = (
            materialized_cells_to_cell_delta(materialization.layout, self._ctx)
            if materialization.layout is not None
            else ()
        )
        map_view = ReplayMapView(
            bbox=bbox_from_replay_cells(cells, cell_delta=cell_delta),
            full_cells=cells,
            cell_delta=cell_delta,
        )
        mat_count = len(materialization.layout.cells) if materialization.layout else 0
        self._append(
            phase=ReplayPhase.RESULT,
            event_type=ReplayEventType.RESULT_LAYOUT,
            title="Final Layout",
            description=(
                f"confirmed={len(commit.confirmed)}, " f"validation_passed={validation.passed}"
            ),
            map_view=map_view,
            inspector={
                "confirmed_count": len(commit.confirmed),
                "validation_passed": validation.passed,
                "issue_codes": list(solver_summary.get("issue_codes") or []),
                "materialized_cell_count": mat_count,
            },
        )

    def build_frames(self) -> tuple[ReplayTimelineFrame, ...]:
        """Return recorded frames in recording order (output-only; never solver input)."""
        return tuple(self._frames)


__all__ = ["SolverRuntimeReplayRecorder"]
