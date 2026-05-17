"""Import vs algorithm coordinate boundaries (Sequence 12L)."""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_ALGORITHM_COORD_TOKENS = (
    "raw_to_server",
    "server_to_raw",
    "server_xy_for_raw_xy",
    "raw_x_to_dense_x",
    "asteroid_lab.snapshots.server_coords",
    "raw_x",
    "raw_y",
    "raw_coord",
    "visual_coord",
)

# Raw↔dense projection lives in decode/snapshot boundaries; algorithm must not bind it.
_FORBIDDEN_COORD_PROJECTION_MODULES: frozenset[str] = frozenset(
    {
        "django_apps.asteroid_lab.snapshots.server_coords",
        "django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot",
    }
)


def _imported_module_strings(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
            for alias in node.names:
                if alias.name != "*":
                    out.add(f"{node.module}.{alias.name}")
    return out


def _algorithm_projection_boundary_paths(repo: Path) -> list[Path]:
    roots = [
        repo / "django_apps" / "shapez_asteroid" / "optimization",
        repo / "django_apps" / "web" / "services" / "asteroid_lab_post_inspection_evolution.py",
        repo / "django_apps" / "shapez_asteroid" / "adapters" / "reconstruction_adapter.py",
    ]
    paths: list[Path] = []
    for root in roots:
        paths.extend([root] if root.is_file() else sorted(root.rglob("*.py")))
    opt_services = repo / "django_apps" / "asteroid_lab" / "services"
    paths.extend(sorted(opt_services.glob("*optimization*.py")))
    return paths


def _assert_no_forbidden_projection_imports(path: Path, repo: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported = _imported_module_strings(tree)
    for mod in sorted(imported):
        for forbidden in _FORBIDDEN_COORD_PROJECTION_MODULES:
            if mod == forbidden or mod.startswith(forbidden + "."):
                rel = path.relative_to(repo)
                raise AssertionError(
                    f"{rel}: forbidden coordinate projection import {mod!r} "
                    f"(matches {forbidden!r})"
                )


def test_algorithm_modules_do_not_import_coordinate_projection_boundary() -> None:
    """Token scans miss renamed helpers; block snapshot projection modules at import sites."""

    repo = Path(__file__).resolve().parents[3]
    for path in _algorithm_projection_boundary_paths(repo):
        _assert_no_forbidden_projection_imports(path, repo)


def test_optimization_package_has_no_raw_to_server_bridge() -> None:
    """Algorithm tree must not import raw/server conversion helpers."""

    repo = Path(__file__).resolve().parents[3]
    root = repo / "django_apps" / "shapez_asteroid" / "optimization"
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_ALGORITHM_COORD_TOKENS:
            assert token not in text, f"{path.relative_to(repo)} must not contain {token!r}"


def test_post_inspection_evolution_has_no_raw_coord_bridge() -> None:
    repo = Path(__file__).resolve().parents[3]
    path = repo / "django_apps" / "web" / "services" / "asteroid_lab_post_inspection_evolution.py"
    text = path.read_text(encoding="utf-8")
    for token in FORBIDDEN_ALGORITHM_COORD_TOKENS:
        assert token not in text, f"post_inspection evolution must not contain {token!r}"


def test_asteroid_lab_optimization_services_have_no_raw_coord_bridge() -> None:
    repo = Path(__file__).resolve().parents[3]
    root = repo / "django_apps" / "asteroid_lab" / "services"
    for path in sorted(root.glob("*optimization*.py")):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_ALGORITHM_COORD_TOKENS:
            assert token not in text, f"{path.relative_to(repo)} must not contain {token!r}"


def test_optimization_adapter_has_no_raw_coord_bridge() -> None:
    repo = Path(__file__).resolve().parents[3]
    path = repo / "django_apps" / "shapez_asteroid" / "adapters" / "reconstruction_adapter.py"
    text = path.read_text(encoding="utf-8")
    forbidden = (
        "raw_to_server",
        "server_to_raw",
        "server_xy_for_raw_xy",
        "raw_x_to_dense_x",
        "Cannot map raw",
        "raw_coord",
        "visual_coord",
    )
    for token in forbidden:
        assert token not in text, f"optimization adapter must not contain {token!r}"
