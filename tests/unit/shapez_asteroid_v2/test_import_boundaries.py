"""Import boundaries: v2 must stay isolated from v1 and from replay in core steps."""

from __future__ import annotations

import ast
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_V2_PKG = _REPO_ROOT / "django_apps" / "shapez_asteroid" / "services" / "asteroid_mining_layout_v2"

_LEGACY_ABS = "django_apps.shapez_asteroid.services.asteroid_mining_layout."
_LEGACY_TAIL = "django_apps.shapez_asteroid.services.asteroid_mining_layout"


def _py_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _legacy_reference_in_line(line: str) -> bool:
    s = line.split("#", 1)[0]
    if "asteroid_mining_layout_v2" in s:
        return False
    if _LEGACY_ABS in s:
        return True
    if _LEGACY_TAIL in s and "asteroid_mining_layout_v2" not in s:
        # import ... asteroid_mining_layout (exact end) or import ... as
        return bool(re.search(rf"{re.escape(_LEGACY_TAIL)}(\s|$|,)", s))
    return False


def _replay_import_in_line(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith("#"):
        return False
    if not (s.startswith("import ") or s.startswith("from ")):
        return False
    return bool(re.search(r"\breplay\b", s))


def test_v2_sources_do_not_reference_legacy_asteroid_mining_layout() -> None:
    offenders: list[str] = []
    for path in _py_files(_V2_PKG):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _legacy_reference_in_line(line):
                offenders.append(f"{path}:{i}:{line.strip()}")
    assert not offenders, "v2 must not reference v1 layout package:\n" + "\n".join(offenders)


def test_placement_routing_validation_do_not_import_replay() -> None:
    offenders: list[str] = []
    for sub in ("placement", "routing", "validation"):
        for path in _py_files(_V2_PKG / sub):
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if _replay_import_in_line(line):
                    offenders.append(f"{path}:{i}:{line.strip()}")
    assert not offenders, "placement/routing/validation must not import replay:\n" + "\n".join(
        offenders
    )


def test_validation_does_not_import_merge_aware_router() -> None:
    pat = re.compile(r"merge_aware_router")
    for path in _py_files(_V2_PKG / "validation"):
        text = path.read_text(encoding="utf-8")
        assert not pat.search(text), f"{path} must not reference merge_aware_router"


def test_v2_tree_has_no_django_imports() -> None:
    offenders: list[str] = []
    for path in _py_files(_V2_PKG):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    n = alias.name
                    if n == "django" or n.startswith("django."):
                        offenders.append(f"{path}: import {n}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                m = node.module
                if m == "django" or m.startswith("django."):
                    offenders.append(f"{path}: from {m}")
    assert not offenders, "v2 must remain Django-free:\n" + "\n".join(offenders)


_V1_LAYOUT_PKG = "django_apps.shapez_asteroid.services.asteroid_mining_layout"


def _imports_v1_layout_module(module_name: str) -> bool:
    """True if ``module_name`` is the legacy v1 package (not ``...layout_v2``)."""

    if module_name == _V1_LAYOUT_PKG:
        return True
    return module_name.startswith(_V1_LAYOUT_PKG + ".")


def test_solver_py_does_not_import_v1_layout_package() -> None:
    solver_path = _V2_PKG / "solver.py"
    tree = ast.parse(solver_path.read_text(encoding="utf-8"), filename=str(solver_path))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _imports_v1_layout_module(alias.name):
                    offenders.append(f"{solver_path}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if _imports_v1_layout_module(node.module):
                offenders.append(f"{solver_path}: from {node.module}")
    assert not offenders, "solver.py must not import v1 layout internals:\n" + "\n".join(offenders)


def test_v2_domain_imports_without_django_in_subprocess() -> None:
    """Smoke: enum module must not pull Django onto ``sys.modules``."""

    import subprocess
    import sys

    root_repr = repr(str(_REPO_ROOT))
    code = f"""
import sys
sys.path.insert(0, {root_repr})
import django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums as e
assert not any(m.startswith("django.") for m in sys.modules if m.startswith("django"))
print(e.TransportKind.SHAPE_BELT.value)
"""
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
