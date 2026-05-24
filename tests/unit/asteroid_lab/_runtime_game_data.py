"""Test helpers: RTTP runtime with pinned game_data provenance."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SolverRuntimeEntryResult,
    run_solver_runtime_for_project,
)
from django_apps.web.services.asteroid_game_data_snapshot import (
    build_asteroid_game_data_snapshot_with_provenance,
)


def run_solver_runtime_with_pinned_game_data(
    project_id: int,
    /,
    **kwargs: Any,
) -> SolverRuntimeEntryResult:
    """Build snapshot+provenance once, then call runtime entry (RTTP tests)."""

    build = build_asteroid_game_data_snapshot_with_provenance()
    return run_solver_runtime_for_project(
        project_id,
        game_data_snapshot=build.snapshot,
        game_data_provenance=build.provenance,
        catalog_slice=build.catalog_slice,
        **kwargs,
    )
