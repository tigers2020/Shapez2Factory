"""Import boundaries: v2 must stay isolated from v1 and from replay in core steps.

v1 ``asteroid_mining_layout``: 소스 줄 스캔 + AST(절대·상대 ``from`` 해석)로 이중 검사.
django_apps.* 교차 import allowlist.
우발적 레거시/타 앱 의존 차단; 추가 시 본 목록과 근거를 갱신할 것.

- ``django_apps.shapez_asteroid.services.asteroid_mining_layout_v2`` — v2 자기 참조.
- ``django_apps.shapez_asteroid.services.blueprint_entry_parsing`` — 블루프린트 엔트리 파싱 공용.
- ``django_apps.shapez_asteroid.services.style_classifier`` — 레이아웃 스타일 분류.
- ``django_apps.shapez_asteroid.services.behavior_artifact_collector`` —
  솔버 행위 아티팩트 수집(출력 경로).
- ``django_apps.shapez_asteroid.constants`` — COPY_PREVIEW_SCHEMA_VERSION 등 앱 상수.
- ``django_apps.shapez_asteroid.extraction.shape_miner_rotation`` — 프리뷰 타임라인 채굴 회전.
- ``django_apps.shapez_core.services.shapez_copy_decode`` — 세이브 복호화/디코드 DTO.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_V2_PKG = _REPO_ROOT / "django_apps" / "shapez_asteroid" / "services" / "asteroid_mining_layout_v2"
_V2_SERVICES_PKG = "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2"
_REPLAY_PKG = f"{_V2_SERVICES_PKG}.replay"
_ROUTING_PKG = f"{_V2_SERVICES_PKG}.routing"
_ALLOWED_VALIDATION_ROUTING = f"{_ROUTING_PKG}.connectivity"

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


def test_v2_sources_do_not_reference_legacy_asteroid_mining_layout() -> None:
    offenders: list[str] = []
    for path in _py_files(_V2_PKG):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _legacy_reference_in_line(line):
                offenders.append(f"{path}:{i}:{line.strip()}")
    assert not offenders, "v2 must not reference v1 layout package:\n" + "\n".join(offenders)


def _imports_replay_package(module_name: str) -> bool:
    return module_name == _REPLAY_PKG or module_name.startswith(_REPLAY_PKG + ".")


def _replay_import_offenders_in_file(path: Path) -> list[str]:
    bad: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _imports_replay_package(alias.name):
                    bad.append(f"{path}:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            base = _import_from_base_module(path, node)
            if base is not None and _imports_replay_package(base):
                bad.append(f"{path}:{node.lineno}: from {base}")
            elif base is not None:
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    full = f"{base}.{alias.name}"
                    if _imports_replay_package(full):
                        bad.append(
                            f"{path}:{node.lineno}: from {base} import {alias.name} -> {full}"
                        )
    return bad


def test_core_algorithm_tree_does_not_import_replay_package_ast() -> None:
    """Replay/NDJSON reader lives under ``replay``; domain/placement/routing/validation must not."""

    roots = [
        _V2_PKG / "domain",
        _V2_PKG / "placement",
        _V2_PKG / "routing",
        _V2_PKG / "validation",
        _V2_PKG / "reconstruction",
        _V2_PKG / "decode",
        _V2_PKG / "serialization",
    ]
    offenders: list[str] = []
    for root in roots:
        for path in _py_files(root):
            offenders.extend(_replay_import_offenders_in_file(path))
    assert not offenders, "core v2 must not import replay package:\n" + "\n".join(offenders)


def _is_routing_submodule_path(module_path: str) -> bool:
    return module_path == _ROUTING_PKG or module_path.startswith(_ROUTING_PKG + ".")


def _allowed_routing_module_for_validation(module_path: str) -> bool:
    return module_path == _ALLOWED_VALIDATION_ROUTING or module_path.startswith(
        _ALLOWED_VALIDATION_ROUTING + "."
    )


def _forbidden_routing_import_for_validation(module_path: str) -> bool:
    if not _is_routing_submodule_path(module_path):
        return False
    return not _allowed_routing_module_for_validation(module_path)


def _validation_routing_import_offenders_in_file(path: Path) -> list[str]:
    bad: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _forbidden_routing_import_for_validation(alias.name):
                    bad.append(f"{path}:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            base = _import_from_base_module(path, node)
            if base is None or not _is_routing_submodule_path(base):
                continue
            if base == _ROUTING_PKG:
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    full = f"{base}.{alias.name}"
                    if _forbidden_routing_import_for_validation(full):
                        bad.append(
                            f"{path}:{node.lineno}: from {base} import {alias.name} -> {full}"
                        )
            else:
                if _forbidden_routing_import_for_validation(base):
                    bad.append(f"{path}:{node.lineno}: from {base}")
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    full = f"{base}.{alias.name}"
                    if _forbidden_routing_import_for_validation(full):
                        bad.append(
                            f"{path}:{node.lineno}: from {base} import {alias.name} -> {full}"
                        )
    return bad


def test_validation_only_imports_routing_connectivity_subtree() -> None:
    offenders: list[str] = []
    for path in _py_files(_V2_PKG / "validation"):
        offenders.extend(_validation_routing_import_offenders_in_file(path))
    assert not offenders, "validation may only use routing.connectivity:\n" + "\n".join(offenders)


_BAD_BEHAVIOR_ARTIFACT_MODULES = frozenset(
    {
        "django_apps.shapez_asteroid.services.behavior_artifact_collector",
        "django_apps.shapez_asteroid.services.v2_behavior_artifact_dump",
    }
)


def _import_targets_bad(module_name: str | None) -> bool:
    if module_name is None:
        return False
    if module_name in _BAD_BEHAVIOR_ARTIFACT_MODULES:
        return True
    return any(module_name.startswith(m + ".") for m in _BAD_BEHAVIOR_ARTIFACT_MODULES)


def test_core_v2_modules_do_not_import_behavior_artifact_stack() -> None:
    """Behavior artifacts are output-only; domain / pass1 / recon core must not depend on them."""

    roots = [
        _V2_PKG / "domain",
        _V2_PKG / "placement" / "pass1_outer.py",
        _V2_PKG / "reconstruction" / "asteroid_reconstruction.py",
        _V2_PKG / "routing",
        _V2_PKG / "validation",
    ]
    offenders: list[str] = []
    for root in roots:
        paths = [root] if root.is_file() else _py_files(root)
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if _import_targets_bad(alias.name):
                            offenders.append(f"{path}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if _import_targets_bad(node.module):
                        offenders.append(f"{path}: from {node.module}")
    assert not offenders, "forbidden behavior-artifact imports:\n" + "\n".join(offenders)


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


def _containing_package_for_v2_py(path: Path) -> str:
    """``__package__``-equivalent dotted name for a ``.py`` file under ``_V2_PKG``."""

    rel = path.relative_to(_V2_PKG)
    parent = rel.parent
    parts: list[str] = [] if parent == Path(".") else list(parent.parts)
    pkg = _V2_SERVICES_PKG
    for p in parts:
        pkg = f"{pkg}.{p}"
    return pkg


def _import_from_base_module(path: Path, node: ast.ImportFrom) -> str | None:
    """Absolute dotted name of the module targeted by ``from … import`` (``None`` if invalid)."""

    pkg = _containing_package_for_v2_py(path)
    if node.level == 0:
        return node.module
    rel = "." * node.level + (node.module if node.module else "")
    try:
        return importlib.util.resolve_name(rel, pkg)
    except ImportError:
        return None


def test_v2_tree_has_no_ast_import_from_v1_layout_package() -> None:
    """AST: 절대·상대 import 모두에서 v1 ``asteroid_mining_layout`` 금지 (문자열 스캔 보완)."""

    offenders: list[str] = []
    for path in _py_files(_V2_PKG):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _imports_v1_layout_module(alias.name):
                        offenders.append(f"{path}:{node.lineno}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                base = _import_from_base_module(path, node)
                if base is None:
                    rel = "." * node.level + (node.module or "")
                    offenders.append(
                        f"{path}:{node.lineno}: invalid relative import {rel!r} "
                        f"(package {_containing_package_for_v2_py(path)})"
                    )
                elif _imports_v1_layout_module(base):
                    offenders.append(f"{path}:{node.lineno}: from {base}")
    assert not offenders, "v2 must not import v1 layout package:\n" + "\n".join(offenders)


_ASTEROID_SERVICES_PREFIX = "django_apps.shapez_asteroid.services."
_ALLOWED_NON_V2_SERVICE_TOPLEVEL = frozenset(
    {
        "blueprint_entry_parsing",
        "style_classifier",
        "behavior_artifact_collector",
    }
)
_SHAPEZ_CORE_COPY_DECODE = "django_apps.shapez_core.services.shapez_copy_decode"
_EXTRACTION_SHAPE_MINER_ROTATION = "django_apps.shapez_asteroid.extraction.shape_miner_rotation"


def _allowed_django_apps_module(module: str) -> bool:
    """True if ``module`` is an allowed cross-package ``django_apps.*`` import for v2."""

    if module == _V2_SERVICES_PKG or module.startswith(_V2_SERVICES_PKG + "."):
        return True

    if module.startswith(_ASTEROID_SERVICES_PREFIX):
        remainder = module.removeprefix(_ASTEROID_SERVICES_PREFIX)
        if not remainder:
            return False
        top = remainder.split(".", 1)[0]
        return top in _ALLOWED_NON_V2_SERVICE_TOPLEVEL

    if module.startswith("django_apps.shapez_asteroid."):
        if module == "django_apps.shapez_asteroid.constants" or module.startswith(
            "django_apps.shapez_asteroid.constants."
        ):
            return True
        if module == _EXTRACTION_SHAPE_MINER_ROTATION or module.startswith(
            _EXTRACTION_SHAPE_MINER_ROTATION + "."
        ):
            return True
        return False

    if module.startswith("django_apps.shapez_core."):
        dec = _SHAPEZ_CORE_COPY_DECODE
        return module == dec or module.startswith(dec + ".")

    return False


def _django_apps_import_offenders_in_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name.startswith("django_apps.") and not _allowed_django_apps_module(name):
                    bad.append(f"{path}:{node.lineno}:import {name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            m = node.module
            if m.startswith("django_apps.") and not _allowed_django_apps_module(m):
                bad.append(f"{path}:{node.lineno}:from {m}")
    return bad


def test_v2_tree_django_apps_imports_match_allowlist() -> None:
    offenders: list[str] = []
    for path in _py_files(_V2_PKG):
        offenders.extend(_django_apps_import_offenders_in_file(path))
    assert not offenders, "v2 django_apps import allowlist violated:\n" + "\n".join(offenders)


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
