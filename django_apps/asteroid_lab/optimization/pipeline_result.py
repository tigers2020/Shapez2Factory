"""Solver Runtime A→M pipeline result DTO (PR7)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.optimization.commit_best_candidates import IncrementalCommitResult
from django_apps.asteroid_lab.optimization.input_contracts import ValidationResult
from django_apps.asteroid_lab.optimization.materialization_dtos import RouteMaterializationResult
from django_apps.asteroid_lab.optimization.replay_frame import OptimizationReplayFrame


@dataclass(frozen=True, slots=True)
class SolverRuntimeResult:
    """In-memory outcome of ``run_solver_runtime_pipeline`` (before optional persist)."""

    run_key: str
    commit: IncrementalCommitResult
    materialization: RouteMaterializationResult
    validation: ValidationResult
    solver_summary: dict[str, Any]
    replay_frames: tuple[OptimizationReplayFrame, ...]
