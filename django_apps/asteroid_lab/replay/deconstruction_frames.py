"""Replay helpers: load cleanup / deconstruction result for timeline assembly."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO


def load_cleanup_result(
    snapshot: DecodedBlueprintSnapshotDTO,
    *,
    boundary_run_id: str | None = None,
) -> CleanupResult:
    """Run pre-reconstruction cleanup on a decoded snapshot."""

    return deconstruct_snapshot(snapshot, boundary_run_id=boundary_run_id)
