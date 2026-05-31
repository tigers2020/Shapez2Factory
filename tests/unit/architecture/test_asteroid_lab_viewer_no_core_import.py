"""Architecture gate for the Django run-solver request path."""

from __future__ import annotations

import ast
from pathlib import Path

REQUEST_PATH_FILES = [
    "django_apps/asteroid_lab/services/solver_runtime_entry.py",
    "django_apps/asteroid_lab/services/solver_subprocess_runner.py",
    "django_apps/asteroid_lab/services/artifact_ingest.py",
    "django_apps/asteroid_lab/services/artifact_manifest_reader.py",
    "django_apps/web/views/public_pages.py",
]

ALLOWED_CORE_MODULE_STRINGS = {
    "shapez2_factory.interfaces.cli.asteroid_solve",
}

REPLAY_VIEWER_FILES = [
    "django_apps/asteroid_lab/replay",
]

# Viewer/replay may use pure domain helpers; must not pull solver execution stack.
REPLAY_ALLOWED_CORE_PREFIXES = (
    "shapez2_factory.application.asteroid_lab.layers.contracts",
    "shapez2_factory.domain.asteroid_lab.reconstruction.complete_map_merge",
    "shapez2_factory.domain.asteroid_lab.grid_contract",
    "shapez2_factory.domain.asteroid_lab.reconstruction.complete_map",
)

FORBIDDEN_REPLAY_CORE_PREFIXES = (
    "shapez2_factory.application",
    "shapez2_factory.interfaces",
    "shapez2_factory.adapters.asteroid_lab",
)

LAYER_SHIM_FREE_DIRS = [
    "django_apps/asteroid_lab/replay",
    "django_apps/asteroid_lab/services",
]


def _imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
    return modules


def _constant_strings(tree: ast.AST) -> list[str]:
    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append(node.value)
    return values


def test_django_run_solver_request_path_does_not_import_solver_core() -> None:
    root = Path(__file__).resolve().parents[3]
    offenders: list[str] = []
    for relpath in REQUEST_PATH_FILES:
        path = root / relpath
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for module in _imported_modules(tree):
            if module.startswith("shapez2_factory"):
                offenders.append(f"{relpath}: import {module}")

    assert offenders == []


def test_subprocess_runner_references_cli_by_string_only() -> None:
    root = Path(__file__).resolve().parents[3]
    path = root / "django_apps/asteroid_lab/services/solver_subprocess_runner.py"
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))

    assert ALLOWED_CORE_MODULE_STRINGS.issubset(set(_constant_strings(tree)))
    assert all(not module.startswith("shapez2_factory") for module in _imported_modules(tree))


def test_solver_runtime_entry_does_not_import_legacy_in_process_runtime() -> None:
    root = Path(__file__).resolve().parents[3]
    path = root / "django_apps/asteroid_lab/services/solver_runtime_entry.py"
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))

    imported = set(_imported_modules(tree))

    assert "django_apps.asteroid_lab.services.solver_runtime_layer02" not in imported


def test_replay_modules_do_not_import_solver_execution_core() -> None:
    root = Path(__file__).resolve().parents[3]
    replay_dir = root / "django_apps/asteroid_lab/replay"
    offenders: list[str] = []
    for path in sorted(replay_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for module in _imported_modules(tree):
            if not module.startswith("shapez2_factory"):
                continue
            if module.startswith(REPLAY_ALLOWED_CORE_PREFIXES):
                continue
            if module.startswith(FORBIDDEN_REPLAY_CORE_PREFIXES):
                offenders.append(f"{path.relative_to(root)}: import {module}")
    assert offenders == []


def test_viewer_services_do_not_import_django_layer_shims() -> None:
    root = Path(__file__).resolve().parents[3]
    offenders: list[str] = []
    for rel_dir in LAYER_SHIM_FREE_DIRS:
        for path in sorted((root / rel_dir).glob("*.py")):
            if path.name == "__init__.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            for module in _imported_modules(tree):
                if module.startswith("django_apps.asteroid_lab.layers"):
                    offenders.append(f"{path.relative_to(root)}: import {module}")
    assert offenders == []
