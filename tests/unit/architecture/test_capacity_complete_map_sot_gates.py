"""Capacity C-GATE — complete-map SoT architecture gates (G1 + G2).

Spec: docs/superpowers/specs/2026-05-29-reconstruction-capacity-c-gate-design.md
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LAB_ROOT = _REPO_ROOT / "django_apps" / "asteroid_lab"

_FORBIDDEN_SYMBOLS: frozenset[str] = frozenset(
    {
        "mineable_coords_from_reconstruction",
        "external_void_coords_from_reconstruction",
        "asteroid_field_cells_from_reconstruction",
    }
)

_G1_SCAN_REL_PATHS: tuple[str, ...] = (
    "optimization",
    "services/solver_runtime_entry.py",
    "services/reconstruction_capacity_summary.py",
)

_DECISION_SUBDIRS: frozenset[str] = frozenset(
    {
        "commit",
        "selection",
        "routing",
        "candidates",
        "validation",
        "macros",
        "skeleton",
    }
)

# G1 scans reconstruction_capacity_summary.py for forbidden overlay imports.
# G2 excludes it — complete-map envelope authority (spec §5 G2).
_G2_EXCLUDED_REL: frozenset[str] = frozenset(
    {
        "optimization/pipeline.py",
        "optimization/rttp_solver_summary.py",
        "optimization/rttp_replay_diagnostics.py",
        "optimization/replay_sink.py",
        "services/reconstruction_capacity_summary.py",
    }
)

_FORBIDDEN_CALLEE_SUBSTRINGS: frozenset[str] = frozenset(
    {
        "mineable",
        "field_cell",
        "capacity",
        "platform_count",
    }
)

_RECON_RESULT_PARAM_NAMES: frozenset[str] = frozenset({"recon", "result", "reconstruction"})


def _g1_py_files() -> list[Path]:
    out: list[Path] = []
    for rel in _G1_SCAN_REL_PATHS:
        path = _LAB_ROOT / rel
        if path.is_file():
            out.append(path)
            continue
        out.extend(sorted(path.rglob("*.py")))
    return out


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def _rel(path: Path) -> str:
    return path.relative_to(_LAB_ROOT).as_posix()


def _imported_names(tree: ast.Module) -> list[tuple[str, int]]:
    names: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.append((alias.name, node.lineno))
    return names


def _forbidden_calls(tree: ast.Module) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "acceptance_topology_from_reconstruction":
                hits.append(f"L{node.lineno}: call acceptance_topology_from_reconstruction")
    return hits


def _g2_scan_files() -> list[Path]:
    opt = _LAB_ROOT / "optimization"
    out: list[Path] = []
    for sub in sorted(_DECISION_SUBDIRS):
        root = opt / sub
        if root.is_dir():
            out.extend(sorted(root.rglob("*.py")))
    for rel in (
        "optimization/reconstruction_adapter.py",
        "services/solver_runtime_entry.py",
    ):
        path = _LAB_ROOT / rel
        if path.is_file():
            out.append(path)
    return [path for path in out if _rel(path) not in _G2_EXCLUDED_REL]


def _is_recon_cells(node: ast.AST, param_names: frozenset[str]) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "cells"
        and isinstance(node.value, ast.Name)
        and node.value.id in param_names
    )


def _forbidden_recon_cells_usage(tree: ast.Module, *, rel: str) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = node.value
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "mineable_cells":
                    if _is_recon_cells(value, _RECON_RESULT_PARAM_NAMES) or (
                        isinstance(value, ast.Call)
                        and isinstance(value.func, ast.Name)
                        and any(s in value.func.id for s in _FORBIDDEN_CALLEE_SUBSTRINGS)
                    ):
                        hits.append(
                            f"{rel}:L{node.lineno}: mineable_cells assigned from overlay path"
                        )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if any(s in node.func.id for s in _FORBIDDEN_CALLEE_SUBSTRINGS):
                for arg in node.args:
                    if _is_recon_cells(arg, _RECON_RESULT_PARAM_NAMES):
                        hits.append(f"{rel}:L{node.lineno}: recon.cells passed to {node.func.id}")
    return hits


def test_g1_no_overlay_mineable_imports_in_scanned_roots() -> None:
    violations: list[str] = []
    for path in _g1_py_files():
        tree = _parse(path)
        rel = _rel(path)
        for name, lineno in _imported_names(tree):
            if name in _FORBIDDEN_SYMBOLS:
                violations.append(f"{rel}:{lineno}: imports forbidden symbol {name!r}")
        for hit in _forbidden_calls(tree):
            violations.append(f"{rel}:{hit}")
    assert not violations, "\n".join(violations)


def test_g2_no_overlay_cells_on_decision_capacity_paths() -> None:
    violations: list[str] = []
    for path in _g2_scan_files():
        rel = _rel(path)
        tree = _parse(path)
        violations.extend(_forbidden_recon_cells_usage(tree, rel=rel))
    assert not violations, "\n".join(violations)
