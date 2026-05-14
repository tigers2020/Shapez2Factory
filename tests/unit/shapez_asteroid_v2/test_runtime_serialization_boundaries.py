"""Layering: algorithm modules must not depend on preview / artifact builders."""

from __future__ import annotations

import ast
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_V2 = _REPO_ROOT / "django_apps" / "shapez_asteroid" / "services" / "asteroid_mining_layout_v2"


def _py_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


_FORBIDDEN_ALGO_IMPORT_SUBSTR = (
    "preview_reconstruction_timeline",
    "behavior_artifact_collector",
    "v2_behavior_artifact_dump",
)


def _line_targets_forbidden_algo_deps(line: str) -> bool:
    s = line.split("#", 1)[0].strip()
    if not s.startswith(("import ", "from ")):
        return False
    return any(tok in s for tok in _FORBIDDEN_ALGO_IMPORT_SUBSTR)


def test_algorithm_trees_do_not_import_preview_or_behavior_artifacts() -> None:
    """Domain / placement / routing / validation / core reconstruction avoid UI-output stack."""

    roots = [
        _V2 / "domain",
        _V2 / "placement",
        _V2 / "routing",
        _V2 / "validation",
        _V2 / "reconstruction" / "asteroid_reconstruction.py",
        _V2 / "reconstruction" / "patch_interior.py",
    ]
    offenders: list[str] = []
    for root in roots:
        paths = [root] if root.is_file() else _py_files(root)
        for path in paths:
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if _line_targets_forbidden_algo_deps(line):
                    offenders.append(f"{path}:{i}:{line.strip()}")
    assert not offenders, "algorithm layers must not import preview/artifacts:\n" + "\n".join(
        offenders
    )


def _assert_py_file_has_no_django_imports(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    offenders: list[str] = []
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
    assert not offenders, "\n".join(offenders)


def test_serialization_json_safe_has_no_django_imports() -> None:
    _assert_py_file_has_no_django_imports(_V2 / "serialization" / "json_safe.py")


def test_serialization_public_artifacts_has_no_django_imports() -> None:
    _assert_py_file_has_no_django_imports(_V2 / "serialization" / "public_artifacts.py")


def test_serialization_dto_adapters_has_no_django_imports() -> None:
    _assert_py_file_has_no_django_imports(_V2 / "serialization" / "dto_adapters.py")


def _assert_tree_has_no_serialization_imports(root: Path, label: str) -> None:
    pat = re.compile(r"asteroid_mining_layout_v2\.serialization")
    for path in _py_files(root):
        text = path.read_text(encoding="utf-8")
        assert not pat.search(text), f"{label}: {path} must not import v2.serialization"


def test_placement_does_not_import_serialization_public_stack() -> None:
    """Placement stays free of JSON artifact adapters (Pass1 input stays domain DTO)."""

    _assert_tree_has_no_serialization_imports(_V2 / "placement", "placement")


def test_routing_does_not_import_serialization_public_stack() -> None:
    _assert_tree_has_no_serialization_imports(_V2 / "routing", "routing")


def test_validation_does_not_import_serialization_public_stack() -> None:
    _assert_tree_has_no_serialization_imports(_V2 / "validation", "validation")


def test_domain_does_not_import_serialization_public_stack() -> None:
    _assert_tree_has_no_serialization_imports(_V2 / "domain", "domain")
