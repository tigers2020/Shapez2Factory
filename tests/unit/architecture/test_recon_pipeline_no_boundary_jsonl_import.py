"""PR-CLI-2f — core pipeline must not import the Django boundary sink (BA-1).

The relocated core decode/cleanup/reconstruction modules MUST NOT import ``django``,
``django_apps``, ``config``, or the settings/file-I/O sink ``observability.boundary_jsonl``.
Boundary observability uses an injected ``BoundaryTraceSink``; the Django sink stays Django-side.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_CORE_AL = _REPO / "src" / "shapez2_factory" / "domain" / "asteroid_lab"

_TARGET_CORE_FILES = (
    _CORE_AL / "copy_decode.py",
    _CORE_AL / "normalization.py",
    _CORE_AL / "decoded_blueprint_snapshot.py",
    _CORE_AL / "cell_classifier.py",
    _CORE_AL / "copy_json_coords.py",
    _CORE_AL / "cleanup" / "pipeline.py",
    _CORE_AL / "reconstruction" / "pipeline.py",
    _CORE_AL / "reconstruction" / "confidence.py",
    _CORE_AL / "reconstruction" / "fill.py",
    _CORE_AL / "reconstruction" / "flood_fill.py",
    _CORE_AL / "reconstruction" / "island.py",
    _CORE_AL / "reconstruction" / "perimeter_closing.py",
    _CORE_AL / "reconstruction" / "shell.py",
    _CORE_AL / "reconstruction" / "trace.py",
    _CORE_AL / "reconstruction" / "topology_contract.py",
)

_FORBIDDEN_TOP_LEVEL = ("django", "django_apps", "config")
_FORBIDDEN_SUBSTRINGS = ("observability.boundary_jsonl",)


def _imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
    return modules


def test_target_core_pipeline_files_exist() -> None:
    missing = [str(p.relative_to(_REPO)) for p in _TARGET_CORE_FILES if not p.is_file()]
    assert missing == [], f"core pipeline modules not relocated yet (PR-CLI-2f Step 4): {missing}"


def test_core_pipeline_has_no_django_or_boundary_jsonl_import() -> None:
    violations: list[str] = []
    for path in _TARGET_CORE_FILES:
        if not path.is_file():
            continue  # existence is asserted separately; avoid masking that failure
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for module in _imported_modules(tree):
            top = module.split(".")[0]
            if (
                top in _FORBIDDEN_TOP_LEVEL
                or "django_apps" in module
                or any(sub in module for sub in _FORBIDDEN_SUBSTRINGS)
            ):
                violations.append(f"{path.relative_to(_REPO)} imports {module}")
    assert violations == [], f"core pipeline BA-1 violation: {violations}"
