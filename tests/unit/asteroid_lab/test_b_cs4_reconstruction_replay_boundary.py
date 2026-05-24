"""B-CS4 — reconstruction / Lab replay boundary audit (Axis B).

Spec: docs/superpowers/specs/2026-05-24-b-cs4-reconstruction-replay-boundary-design.md
PASS authority: AST import guards, ReplayFrame ORM call sentinels on persist.
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string, encode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.services.input_service import persist_decoded_snapshot_for_map_input
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    persist_reconstructed_asteroid_map,
    run_reconstruction_for_map_input,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RECONSTRUCTION_PKG = _REPO_ROOT / "django_apps" / "asteroid_lab" / "reconstruction"
_REPLAY_PKG = _REPO_ROOT / "django_apps" / "asteroid_lab" / "replay"

_AUDITED_REPLAY_MODULES = (
    "reconstruction_frames.py",
    "snapshot_map_replay.py",
    "timeline_dtos.py",
    "timeline_serialization.py",
    "event_types.py",
    "replay_enums.py",
)

_RECONSTRUCTION_FORBIDDEN_IMPORT_PREFIXES = (
    "django_apps.asteroid_lab.optimization",
    "django_apps.shapez_solver",
)

_REPLAY_FORBIDDEN_IMPORT_PREFIXES = (
    "django_apps.asteroid_lab.optimization",
    "django_apps.asteroid_lab.services.solver_runtime_entry",
    "django_apps.asteroid_lab.services.solver_runtime_pipeline",
    "django_apps.asteroid_lab.services.lab_rttp_snapshot_compose",
    "django_apps.asteroid_lab.optimization.replay_sink",
    "django_apps.shapez_solver",
    "django_apps.shapez_core",
)

_TRACE_FORBIDDEN_IMPORT_PREFIXES = (
    "django_apps.asteroid_lab.services.solver_runtime_entry",
    "django_apps.asteroid_lab.optimization.replay_sink",
    "django_apps.asteroid_lab.services.lab_rttp_snapshot_compose",
)

_TIMELINE_DTO_FORBIDDEN_IMPORT_PREFIXES = (
    "django_apps.asteroid_lab.models",
    "django_apps.asteroid_lab.services.replay_service",
    "django_apps.asteroid_lab.services.optimization_replay_persist",
    "django_apps.asteroid_lab.services.solver_runtime_pipeline",
    "django_apps.asteroid_lab.services.solver_runtime_entry",
    "django_apps.asteroid_lab.services.runtime_replay_recorder",
)

_TIMELINE_DTO_FORBIDDEN_FRAGMENTS = _TIMELINE_DTO_FORBIDDEN_IMPORT_PREFIXES


def _forbidden_imports(path: Path, prefixes: tuple[str, ...]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                violations.extend(
                    f"{path.name}: import {alias.name}"
                    for p in prefixes
                    if alias.name == p or alias.name.startswith(p + ".")
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            violations.extend(
                f"{path.name}: from {node.module}"
                for p in prefixes
                if node.module == p or node.module.startswith(p + ".")
            )
    return violations


def _py_files_under(pkg: Path) -> list[Path]:
    return sorted(p for p in pkg.rglob("*.py") if p.is_file())


@pytest.mark.parametrize("module_path", _py_files_under(_RECONSTRUCTION_PKG), ids=lambda p: p.name)
def test_b_cs4_reconstruction_package_has_no_optimization_imports(module_path: Path) -> None:
    violations = _forbidden_imports(module_path, _RECONSTRUCTION_FORBIDDEN_IMPORT_PREFIXES)
    assert violations == [], "\n".join(violations)


@pytest.mark.parametrize("module_name", _AUDITED_REPLAY_MODULES)
def test_b_cs4_audited_replay_modules_forbidden_imports_ast(module_name: str) -> None:
    path = _REPLAY_PKG / module_name
    assert path.is_file(), f"missing audited replay module: {module_name}"
    violations = _forbidden_imports(path, _REPLAY_FORBIDDEN_IMPORT_PREFIXES)
    assert violations == [], "\n".join(violations)


@pytest.mark.parametrize(
    "module_name",
    ("reconstruction_frames.py", "snapshot_map_replay.py"),
)
def test_b_cs4_replay_frame_builders_no_optimization_adapter_import(module_name: str) -> None:
    path = _REPLAY_PKG / module_name
    violations = _forbidden_imports(
        path,
        ("django_apps.asteroid_lab.optimization.reconstruction_adapter",)
        + _REPLAY_FORBIDDEN_IMPORT_PREFIXES,
    )
    assert violations == [], "\n".join(violations)


@pytest.fixture
def b_cs4_tiny_copy() -> str:
    root = {
        "V": 21,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
                {"X": 1, "Y": 1, "T": "UnknownTile_A"},
            ],
        },
    }
    return encode_copy_string(root)


@pytest.mark.django_db
def test_b_cs4_persist_does_not_invoke_replay_frame_orm_reads(b_cs4_tiny_copy: str) -> None:
    proj = m.AsteroidProject.objects.create(name="BCS4NoReplay", slug="b-cs4-no-replay-persist")
    inp = m.AsteroidMapInput.objects.create(project=proj, copy_code=b_cs4_tiny_copy)
    norm = normalize_decoded_blueprint(decode_copy_string(b_cs4_tiny_copy.removesuffix("$")))
    persist_decoded_snapshot_for_map_input(inp.id, norm)
    cleanup, recon = run_reconstruction_for_map_input(inp.id)

    with (
        patch.object(m.ReplayFrame.objects, "filter", MagicMock()) as mock_filter,
        patch.object(m.ReplayFrame.objects, "get", MagicMock()) as mock_get,
        patch.object(m.ReplayFrame.objects, "all", MagicMock()) as mock_all,
    ):
        persist_reconstructed_asteroid_map(
            map_input_id=inp.id,
            run_key="b-cs4-no-replay",
            recon=recon,
            cleanup=cleanup,
        )
        mock_filter.assert_not_called()
        mock_get.assert_not_called()
        mock_all.assert_not_called()


@pytest.mark.parametrize(
    "module_name",
    ("timeline_dtos.py", "timeline_serialization.py", "replay_enums.py"),
)
def test_b_cs4_timeline_dto_modules_forbidden_imports_ast(module_name: str) -> None:
    path = _REPLAY_PKG / module_name
    violations = _forbidden_imports(
        path,
        _REPLAY_FORBIDDEN_IMPORT_PREFIXES + _TIMELINE_DTO_FORBIDDEN_IMPORT_PREFIXES,
    )
    assert violations == [], "\n".join(violations)


@pytest.mark.parametrize(
    "module_name",
    ("timeline_dtos.py", "timeline_serialization.py", "replay_enums.py"),
)
def test_b_cs4_timeline_dto_modules_supplementary_fragment_scan(module_name: str) -> None:
    text = (_REPLAY_PKG / module_name).read_text(encoding="utf-8-sig")
    for bad in _TIMELINE_DTO_FORBIDDEN_FRAGMENTS:
        assert bad not in text, f"{module_name} must not reference {bad!r}"


def test_b_cs4_reconstruction_trace_no_debug_algorithm_input_imports() -> None:
    path = _RECONSTRUCTION_PKG / "trace.py"
    violations = _forbidden_imports(path, _TRACE_FORBIDDEN_IMPORT_PREFIXES)
    assert violations == [], "\n".join(violations)
