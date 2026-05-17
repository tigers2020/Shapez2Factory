"""Contract tests for :mod:`tests.unit.shapez_asteroid.fixtures.optimization_json`."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from tests.unit.shapez_asteroid.fixtures.optimization_json import (
    CURRENT_OPTIMIZATION_FIXTURE_SCHEMA_VERSION,
    OptimizationFixtureJsonError,
    load_optimization_fixture_json,
    optimization_fixture_json_to_safe_dict,
    parse_optimization_fixture_json,
)
from tests.unit.shapez_asteroid.test_narrow_corridor_optimization_json_fixtures import (
    _expected_asymmetric,
    _expected_symmetric,
)

_FIX_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "shapez_asteroid" / "optimization"


def test_load_asymmetric_narrow_corridor_fixture_json_contract() -> None:
    path = _FIX_DIR / "narrow_corridor_asymmetric_rim_competition.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    fixture = load_optimization_fixture_json(path)
    safe = optimization_fixture_json_to_safe_dict(fixture)
    assert safe == raw
    assert safe == _expected_asymmetric()


def test_load_symmetric_narrow_corridor_fixture_json_contract() -> None:
    path = _FIX_DIR / "narrow_corridor_symmetric_rim_competition.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    fixture = load_optimization_fixture_json(path)
    safe = optimization_fixture_json_to_safe_dict(fixture)
    assert safe == raw
    assert safe == _expected_symmetric()


def test_fixture_json_rejects_unknown_schema_version() -> None:
    data = dict(_expected_asymmetric())
    data["schema_version"] = CURRENT_OPTIMIZATION_FIXTURE_SCHEMA_VERSION + 1
    with pytest.raises(OptimizationFixtureJsonError, match="unsupported schema_version"):
        parse_optimization_fixture_json(data)


def test_fixture_json_rejects_missing_required_keys() -> None:
    data = dict(_expected_symmetric())
    del data["fixture_id"]
    with pytest.raises(OptimizationFixtureJsonError, match="missing required"):
        parse_optimization_fixture_json(data)

    data2 = dict(_expected_asymmetric())
    del data2["optimization_input"]
    with pytest.raises(OptimizationFixtureJsonError, match="missing required"):
        parse_optimization_fixture_json(data2)


def test_fixture_json_rejects_empty_fixture_id() -> None:
    data = dict(_expected_asymmetric())
    data["fixture_id"] = "   "
    with pytest.raises(OptimizationFixtureJsonError, match="fixture_id"):
        parse_optimization_fixture_json(data)


def test_fixture_json_rejects_unknown_top_level_key() -> None:
    data = dict(_expected_asymmetric())
    data["extra_field"] = 1
    with pytest.raises(OptimizationFixtureJsonError, match="unknown top-level"):
        parse_optimization_fixture_json(data)


def test_fixture_json_coord_shape_is_deterministic() -> None:
    path = _FIX_DIR / "narrow_corridor_asymmetric_rim_competition.json"
    fixture = load_optimization_fixture_json(path)
    cells = fixture.optimization_input["asteroid_cells"]
    assert cells == [{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 2, "y": 0}]
    goal = fixture.primary_route_goal
    assert goal is not None
    assert goal["coord"] == {"x": 2, "y": 0}
    pool = fixture.rim_competition_pool
    assert isinstance(pool, list) and pool
    assert pool[0]["extractor"] == {"x": 0, "y": 0}


def test_fixture_json_contract_does_not_run_solver() -> None:
    import tests.unit.shapez_asteroid.fixtures.optimization_json as optimization_json

    tree = ast.parse(Path(optimization_json.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith(
                "django_apps"
            ), f"unexpected solver-area import: {node.module}"
