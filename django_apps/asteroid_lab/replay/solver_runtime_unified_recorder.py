"""Solver runtime replay recorder: A→M pipeline steps → UnifiedReplayFrame (output-only).

Records optimization pipeline events as UnifiedReplayFrame objects. The resulting
frames are a presentation-only artifact and must never be fed back into the solver.
"""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.optimization.candidate_dtos import CandidateGenerationResult
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
from django_apps.asteroid_lab.replay.replay_recording_cells import (
    bbox_from_replay_cells,
    goal_annotations,
    materialized_cells_to_cell_delta,
    visible_cells_from_loaded_snapshot,
)
from django_apps.asteroid_lab.replay.unified_dtos import (
    ReplayAnnotation,
    ReplayMapView,
    UnifiedReplayFrame,
)
from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType, ReplayPhase


class SolverRuntimeReplayRecorder:
    """Accumulates solver runtime events as UnifiedReplayFrame objects (output-only).

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
        self._frames: list[UnifiedReplayFrame] = []
        # Populated from OptimizationInput.asteroid_cells on first record call.
        # Using opt-input cells gives reliable server-coord coverage even when
        # loaded.cells (recon topology cells) is sparse for simple blueprints.
        self._base_cells_cache: tuple | None = None

    def _cells_from_opt_input(self, inp: OptimizationInput) -> tuple:
        """Convert OptimizationInput asteroid/rim cells to replay cells (server → Lab)."""
        from django_apps.asteroid_lab.replay.unified_dtos import ReplayCell

        coords = sorted(inp.asteroid_cells | inp.rim_cells, key=lambda c: (c[0], c[1]))
        cap = 128  # MAX_SOLVER_RUNTIME_REPLAY_CELLS_PER_FRAME
        out: list[ReplayCell] = []
        for sx, sy in coords:
            x, y = lab_xy_from_server_xy(sx, sy, server_xy_params=self._ctx.server_xy_params)
            out.append(ReplayCell(x=x, y=y, kind="asteroid"))
            if len(out) >= cap:
                break
        return tuple(out)

    @property
    def _base_cells(self) -> tuple:
        if self._base_cells_cache is None:
            # Fallback: use loaded.cells (may be sparse for simple blueprints)
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
            UnifiedReplayFrame(
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
        # Populate base cells from opt-input (server coords, always reliable).
        opt_cells = self._cells_from_opt_input(inp)
        if opt_cells:
            self._base_cells_cache = opt_cells
        cells = self._base_cells
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

    def build_frames(self) -> tuple[UnifiedReplayFrame, ...]:
        """Return recorded frames in recording order (output-only; never solver input)."""
        return tuple(self._frames)


__all__ = ["SolverRuntimeReplayRecorder"]
