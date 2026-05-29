"""Replay authority gate tests (layers must not own runtime replay)."""

from __future__ import annotations

import ast
import pathlib


def test_layers_packages_do_not_import_replay_timeline_frame() -> None:
    root = pathlib.Path("django_apps/asteroid_lab/layers")
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "ReplayTimelineFrame" in {alias.name for alias in node.names}:
                    offenders.append(f"{path}: import from {node.module}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.endswith("ReplayTimelineFrame"):
                        offenders.append(f"{path}: import {alias.name}")
    assert offenders == []


def test_layers_packages_do_not_reference_solver_runtime_replay_frames_key() -> None:
    root = pathlib.Path("django_apps/asteroid_lab/layers")
    needle = "solver_runtime_replay_frames"
    offenders = [
        str(path) for path in root.rglob("*.py") if needle in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
