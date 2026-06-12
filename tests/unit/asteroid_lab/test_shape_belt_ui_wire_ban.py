"""Regression: legacy ``shape_belt`` must not appear in Lab UI / replay wire surfaces."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]

_UI_JS_ROOT = _REPO_ROOT / "django_apps" / "web" / "static" / "web" / "js"
_BANNED_TOKEN = "shape_belt"

# Legacy normalizer is the sole UI file allowed to reference the deprecated token.
_ALLOWED_UI_FILES = frozenset(
    {
        _UI_JS_ROOT / "lab_effective_cell_view.js",
    }
)

_REPLAY_WIRE_ROOTS = (_REPO_ROOT / "tests" / "fixtures" / "asteroid_lab",)

_L3_PRODUCER_PY_ROOTS = (
    _REPO_ROOT / "src" / "shapez2_factory" / "application" / "asteroid_lab" / "layers",
    _REPO_ROOT / "django_apps" / "asteroid_lab" / "replay",
)

_ALLOWED_SHAPE_BELT_PY_FILES = frozenset(
    {
        _REPO_ROOT / "django_apps" / "asteroid_lab" / "replay" / "effective_cell_view.py",
        _REPO_ROOT / "django_apps" / "asteroid_lab" / "replay" / "map_height_layer.py",
        _REPO_ROOT / "django_apps" / "asteroid_lab" / "replay" / "overlay_wire_contract.py",
        _REPO_ROOT
        / "src"
        / "shapez2_factory"
        / "application"
        / "asteroid_lab"
        / "experiments"
        / "transport_kind_normalization.py",
        Path(__file__).resolve(),
        _REPO_ROOT / "tests" / "unit" / "asteroid_lab" / "replay" / "test_effective_cell_view.py",
        _REPO_ROOT / "tests" / "unit" / "asteroid_lab" / "replay" / "test_overlay_wire_contract.py",
        _REPO_ROOT / "tests" / "unit" / "asteroid_lab" / "replay" / "test_map_height_layer.py",
    }
)


def _iter_ui_js_files() -> list[Path]:
    return sorted(p for p in _UI_JS_ROOT.glob("*.js") if p.is_file())


def test_shape_belt_banned_in_lab_ui_js_except_legacy_normalizer() -> None:
    violations: list[str] = []
    for path in _iter_ui_js_files():
        if path in _ALLOWED_UI_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        if _BANNED_TOKEN in text:
            violations.append(str(path.relative_to(_REPO_ROOT)))
    assert not violations, "shape_belt found in UI JS: " + ", ".join(violations)


def _iter_l3_producer_py_files() -> list[Path]:
    files: list[Path] = []
    for root in _L3_PRODUCER_PY_ROOTS:
        if not root.is_dir():
            continue
        files.extend(sorted(p for p in root.rglob("*.py") if p.is_file()))
    return files


def test_shape_belt_banned_in_l3_producer_python_except_legacy_read_paths() -> None:
    violations: list[str] = []
    for path in _iter_l3_producer_py_files():
        if path.resolve() in {p.resolve() for p in _ALLOWED_SHAPE_BELT_PY_FILES}:
            continue
        text = path.read_text(encoding="utf-8")
        if _BANNED_TOKEN in text:
            violations.append(str(path.relative_to(_REPO_ROOT)))
    assert not violations, "shape_belt found in L3/replay producer Python: " + ", ".join(violations)


def test_shape_belt_banned_in_replay_fixture_payloads() -> None:
    violations: list[str] = []
    for root in _REPLAY_WIRE_ROOTS:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.json")):
            if _BANNED_TOKEN in path.read_text(encoding="utf-8"):
                violations.append(str(path.relative_to(_REPO_ROOT)))
    assert not violations, "shape_belt found in replay fixtures: " + ", ".join(violations)


def test_effective_cell_wire_never_emits_shape_belt() -> None:
    from django_apps.asteroid_lab.replay.effective_cell_view import merge_effective_cell_view
    from django_apps.asteroid_lab.replay.effective_cell_wire import effective_cell_to_wire

    view = merge_effective_cell_view(
        x=1,
        y=2,
        full_cell={"x": 1, "y": 2, "kind": "asteroid_shape_field", "transport": "none"},
        overlay_cells=[{"x": 1, "y": 2, "kind": "candidate_miner", "transport": "shape_belt"}],
    )
    assert view is not None
    wire = effective_cell_to_wire(view)
    public = {key: value for key, value in wire.items() if key != "sources"}
    assert _BANNED_TOKEN not in str(public)
    assert wire["output"]["transport_kind"] == "space_belt"
