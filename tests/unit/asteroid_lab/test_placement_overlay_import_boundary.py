"""Placement overlay must not be imported by commit/probe/selection core."""

from __future__ import annotations

from pathlib import Path

_FORBIDDEN_FILES = (
    Path("django_apps/asteroid_lab/optimization/commit/incremental_commit.py"),
    Path("django_apps/asteroid_lab/optimization/commit/incremental_macro_commit.py"),
    Path("django_apps/asteroid_lab/optimization/routing/route_probe.py"),
    Path("django_apps/asteroid_lab/optimization/selection/greedy_regret.py"),
    Path("django_apps/asteroid_lab/optimization/selection/macro_greedy_regret.py"),
)

_ALLOWED_IMPORTER = Path("django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py")


def test_core_modules_do_not_import_placement_overlay_projection() -> None:
    needle = "placement_overlay_projection"
    for path in _FORBIDDEN_FILES:
        source = path.read_text(encoding="utf-8")
        assert needle not in source, f"{path} must not import {needle}"


def test_replay_diagnostics_may_import_placement_overlay_projection() -> None:
    source = _ALLOWED_IMPORTER.read_text(encoding="utf-8")
    assert "placement_overlay_projection" in source
