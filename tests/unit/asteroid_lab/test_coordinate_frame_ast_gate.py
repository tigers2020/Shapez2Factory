"""AST import boundaries for coordinate frame migration (PR-A, extended PR-P2)."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]

# Modules allowed to import ``server_xy_for_raw_xy`` until PR-F (frozen allowlist).
_RECONSTRUCTION_SERVER_XY_ALLOWLIST: frozenset[str] = frozenset(
    {
        "django_apps/asteroid_lab/reconstruction/pipeline.py",
        "django_apps/asteroid_lab/reconstruction/topology_contract.py",
        "django_apps/asteroid_lab/reconstruction/acceptance_topology.py",
        "django_apps/asteroid_lab/reconstruction/confidence.py",
    }
)
_REPLAY_SERVER_XY_ALLOWLIST: frozenset[str] = frozenset(
    {
        "django_apps/asteroid_lab/replay/projection_context.py",
    }
)
_WEB_SERVER_XY_ALLOWLIST: frozenset[str] = frozenset(
    {
        "django_apps/web/services/replay_frame_cell_lookup.py",
    }
)
_OPTIMIZATION_SERVER_XY_ALLOWLIST: frozenset[str] = frozenset()

# PR-F: no server dense bridge symbols in algorithm layer.
_OPTIMIZATION_SERVER_BRIDGE_SYMBOLS: frozenset[str] = frozenset(
    {
        "server_xy_for_raw_xy",
        "attach_server_coords_to_decoded_json",
        "attach_island_coord_meta_to_decoded_json",
        "raw_x_to_dense_index",
        "raw_x_to_dense_x",
    }
)

_ATTACH_SERVER_COORDS_ALLOWLIST: frozenset[str] = frozenset(
    {
        "django_apps/asteroid_lab/snapshots/server_coords.py",
    }
)


def _rel(path: Path) -> str:
    return path.relative_to(_REPO).as_posix()


def _violations_importing(
    root: Path,
    *,
    symbol: str,
    module_substring: str,
    allowlist: frozenset[str],
) -> list[str]:
    if not root.is_dir():
        return []

    found: list[str] = []
    for path in sorted(root.rglob("*.py")):
        rel = _rel(path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            if module_substring not in node.module:
                continue
            for alias in node.names:
                if alias.name != symbol:
                    continue
                if rel not in allowlist:
                    found.append(f"{rel}:{node.lineno}")
    return found


def test_optimization_does_not_import_server_bridge_symbols() -> None:
    root = _REPO / "django_apps" / "asteroid_lab" / "optimization"
    violations: list[str] = []
    for symbol in _OPTIMIZATION_SERVER_BRIDGE_SYMBOLS:
        violations.extend(
            _violations_importing(
                root,
                symbol=symbol,
                module_substring="server_coords",
                allowlist=_OPTIMIZATION_SERVER_XY_ALLOWLIST,
            )
        )
    assert not violations, "server bridge import in optimization: " + ", ".join(violations)


def test_reconstruction_server_xy_imports_match_allowlist() -> None:
    root = _REPO / "django_apps" / "asteroid_lab" / "reconstruction"
    violations = _violations_importing(
        root,
        symbol="server_xy_for_raw_xy",
        module_substring="server_coords",
        allowlist=_RECONSTRUCTION_SERVER_XY_ALLOWLIST,
    )
    assert not violations, "unexpected server_xy_for_raw_xy in reconstruction: " + ", ".join(
        violations
    )


def test_replay_server_xy_imports_match_allowlist() -> None:
    root = _REPO / "django_apps" / "asteroid_lab" / "replay"
    violations = _violations_importing(
        root,
        symbol="server_xy_for_raw_xy",
        module_substring="server_coords",
        allowlist=_REPLAY_SERVER_XY_ALLOWLIST,
    )
    assert not violations, "unexpected server_xy_for_raw_xy in replay: " + ", ".join(violations)


def test_attach_server_coords_import_confined_to_bridge_module() -> None:
    root = _REPO / "django_apps"
    violations = _violations_importing(
        root,
        symbol="attach_server_coords_to_decoded_json",
        module_substring="server_coords",
        allowlist=_ATTACH_SERVER_COORDS_ALLOWLIST,
    )
    assert not violations, "attach_server_coords outside bridge: " + ", ".join(violations)


def test_web_services_server_xy_imports_match_allowlist() -> None:
    root = _REPO / "django_apps" / "web" / "services"
    violations = _violations_importing(
        root,
        symbol="server_xy_for_raw_xy",
        module_substring="server_coords",
        allowlist=_WEB_SERVER_XY_ALLOWLIST,
    )
    assert not violations, "unexpected server_xy_for_raw_xy in web/services: " + ", ".join(
        violations
    )
