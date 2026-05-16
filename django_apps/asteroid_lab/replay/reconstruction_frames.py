"""Replay helpers: topology reconstruction rows for timeline assembly."""

from __future__ import annotations

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.reconstruction.pipeline import reconstruct_after_cleanup
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult


def run_topology_reconstruction(cleanup: CleanupResult) -> ReconstructionResult:
    """Fill enclosed holes from ``CleanupResult`` walls and bbox."""

    return reconstruct_after_cleanup(
        cleaned_cells=cleanup.cleaned_cells,
        wall_coords=cleanup.wall_coords,
        bbox_bounds=cleanup.bbox_bounds,
        server_xy_params=cleanup.server_xy_params,
    )
