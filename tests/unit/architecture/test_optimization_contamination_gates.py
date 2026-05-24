"""PR-B: optimization import canon and decision-path contamination gates.

Spec: docs/superpowers/specs/2026-05-24-decontamination-pr-b-optimization-gates-design.md
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_OPTIMIZATION_ROOT = _REPO_ROOT / "django_apps" / "asteroid_lab" / "optimization"

# Closed set — spec §2.4; new boundary imports require spec amendment.
_ALLOWLIST_EXTRA: frozenset[str] = frozenset(
    {
        "reconstruction_adapter.py",
        "rttp_solver_summary.py",
        "pipeline.py",
        "replay_sink.py",
        "candidates/candidate_generator.py",
        "validation/catalog_layout_validation.py",
    }
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

_TOKEN_EXCLUDE_FILES: frozenset[str] = frozenset(
    {
        "pipeline.py",
        "rttp_solver_summary.py",
        "rttp_replay_diagnostics.py",
        "replay_sink.py",
        "replay_track_keys.py",
        "reconstruction_adapter.py",
        "input_contracts.py",
        "coords.py",
    }
)

_FORBIDDEN_TOKEN_IDS: frozenset[str] = frozenset(
    {
        "solver_summary",
        "ndjson",
        "ReplayFrame",
        "lab_replay_timeline",
    }
)

_SERVICE_ADAPTER_NEEDLES: frozenset[str] = frozenset(
    {
        "lab_optimization_milestone_payload",
        "lab_unified_replay_append",
        "lab_replay_timeline_payload",
    }
)


def _rel(path: Path) -> str:
    return path.relative_to(_OPTIMIZATION_ROOT).as_posix()


def _py_files() -> list[Path]:
    return sorted(_OPTIMIZATION_ROOT.rglob("*.py"))


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def _import_module_strings(tree: ast.Module) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.append((node.module, node.lineno))
    return out


def _module_segments(module: str) -> list[str]:
    return module.split(".")


def _forbidden_import_reason(rel: str, module: str) -> str | None:
    if module.startswith("django_apps.shapez_asteroid") or module.startswith("shapez_asteroid"):
        return "removed shapez_asteroid namespace"
    if "solver_runtime_pipeline" in module:
        return "monolith solver_runtime_pipeline import"
    if "pass_first" in module:
        return "pass_first path"
    if module.startswith("django_apps.asteroid_lab.genetic_sample"):
        return "genetic_sample is non-runtime"
    if module == "django_apps.asteroid_lab.services.lab_rttp_snapshot_compose":
        return "lab_rttp_snapshot_compose belongs on runtime entry only"
    for needle in _SERVICE_ADAPTER_NEEDLES:
        if needle in module:
            return f"replay read adapter {needle!r}"
    if "legacy" in _module_segments(module):
        return "legacy import module segment"
    if module.startswith("django_apps.asteroid_lab.replay"):
        if rel not in {"pipeline.py", "rttp_solver_summary.py"}:
            return "replay package import outside allowlist"
        return None
    if module.startswith("django_apps.asteroid_lab.reconstruction"):
        if rel not in {"reconstruction_adapter.py", "rttp_solver_summary.py"}:
            return "reconstruction import outside allowlist"
        return None
    if module.startswith("django_apps.asteroid_lab.services"):
        if rel not in {"reconstruction_adapter.py", "pipeline.py", "replay_sink.py"}:
            return "services import outside allowlist"
        return None
    if module.startswith("django_apps.asteroid_lab.adapters"):
        tail = module.removeprefix("django_apps.asteroid_lab.adapters.")
        if not tail.startswith("catalog_"):
            return "non-catalog adapter import"
        return None
    return None


def _imports_external_boundary_modules(tree: ast.Module) -> bool:
    prefixes = (
        "django_apps.asteroid_lab.reconstruction",
        "django_apps.asteroid_lab.services",
        "django_apps.asteroid_lab.replay",
        "django_apps.asteroid_lab.adapters",
    )
    for module, _lineno in _import_module_strings(tree):
        if any(module.startswith(p) for p in prefixes):
            return True
    return False


def _docstring_line_ranges(tree: ast.Module) -> list[tuple[int, int]]:
    """Line ranges for module/class/function docstrings (excluded from literal token scan)."""
    ranges: list[tuple[int, int]] = []

    def add_docstring(node: ast.AST) -> None:
        doc = ast.get_docstring(node, clean=False)
        if not doc:
            return
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Constant)
                and isinstance(child.value, str)
                and child.value == doc
            ):
                end = child.end_lineno or child.lineno
                ranges.append((child.lineno, end))
                break

    add_docstring(tree)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            add_docstring(node)
    return ranges


def _lineno_in_ranges(lineno: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= lineno <= end for start, end in ranges)


def _forbidden_tokens_in_tree(tree: ast.Module) -> list[str]:
    doc_ranges = _docstring_line_ranges(tree)
    hits: list[str] = []

    def check_exact(name: str, lineno: int) -> None:
        if name in _FORBIDDEN_TOKEN_IDS:
            hits.append(f"L{lineno}: identifier {name!r}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                check_exact(alias.name, node.lineno)
                if alias.asname:
                    check_exact(alias.asname, node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for segment in _module_segments(node.module):
                check_exact(segment, node.lineno)
            for alias in node.names:
                check_exact(alias.name, node.lineno)
                if alias.asname:
                    check_exact(alias.asname, node.lineno)
        elif isinstance(node, ast.Name):
            check_exact(node.id, node.lineno)
        elif isinstance(node, ast.Attribute):
            check_exact(node.attr, node.lineno)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _lineno_in_ranges(node.lineno, doc_ranges):
                continue
            for token in _FORBIDDEN_TOKEN_IDS:
                if node.value == token:
                    hits.append(f"L{node.lineno}: string literal {token!r}")

    return hits


def _decision_paths() -> list[Path]:
    paths: list[Path] = []
    for path in _py_files():
        rel = _rel(path)
        if rel in _TOKEN_EXCLUDE_FILES:
            continue
        first = rel.split("/", 1)[0]
        if first in _DECISION_SUBDIRS:
            paths.append(path)
    return paths


def test_optimization_imports_respect_forbidden_prefixes_and_allowlist() -> None:
    violations: list[str] = []
    for path in _py_files():
        rel = _rel(path)
        for module, lineno in _import_module_strings(_parse(path)):
            reason = _forbidden_import_reason(rel, module)
            if reason:
                violations.append(f"{rel}:{lineno}: {module!r} — {reason}")
    assert violations == []


def test_optimization_allowlist_files_are_closed_set() -> None:
    offenders: list[str] = []
    for path in _py_files():
        rel = _rel(path)
        if _imports_external_boundary_modules(_parse(path)) and rel not in _ALLOWLIST_EXTRA:
            offenders.append(rel)
    assert (
        offenders == []
    ), "Add file to _ALLOWLIST_EXTRA in spec §2.4 or remove forbidden import: " + ", ".join(
        offenders
    )


def test_optimization_decision_paths_forbid_algorithm_input_tokens() -> None:
    violations: list[str] = []
    for path in _decision_paths():
        rel = _rel(path)
        hits = _forbidden_tokens_in_tree(_parse(path))
        if hits:
            violations.append(f"{rel}: " + "; ".join(hits))
    assert violations == []
