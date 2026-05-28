"""GATE-LS-L2-CAP: no forbidden EVTC numeric literals in selected L2 modules."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_L2_PKG = Path("django_apps/asteroid_lab/layers/layer_02_exterior_transport")
_FORBIDDEN_CAPS = frozenset({720, 8640, 2880, 5760, 480, 345600, 12, 48})
_SCAN_FILES = ("capacity.py", "plan.py", "wire.py", "layout_t.py")


def _numeric_constants(path: Path) -> list[int | float]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: list[int | float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            out.append(node.value)
    return out


@pytest.mark.parametrize("filename", _SCAN_FILES)
def test_layer_02_cap_modules_have_no_forbidden_numeric_literals(filename: str) -> None:
    path = _L2_PKG / filename
    assert path.is_file(), f"missing {path}"
    nums = _numeric_constants(path)
    bad = [n for n in nums if n in _FORBIDDEN_CAPS]
    assert bad == [], f"{filename} contains forbidden cap literals: {bad}"


def test_rotation_py_only_rotation_integers() -> None:
    path = _L2_PKG / "rotation.py"
    nums = _numeric_constants(path)
    assert all(n in {0, 1, 2, 3} for n in nums)
