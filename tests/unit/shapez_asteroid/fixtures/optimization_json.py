"""Strict JSON contract for narrow-corridor optimization golden fixtures (test-only).

``schema_version`` 1 (v0) matches on-disk files under
``tests/fixtures/shapez_asteroid/optimization/``. This module validates structure only;
it does **not** deserialize into domain DTOs and is **not** wired to production solver input.

Top-level shape (mutually exclusive goal export):

- Asymmetric: ``primary_route_goal`` object, no top-level ``route_goals``.
- Symmetric: top-level ``route_goals`` array, no ``primary_route_goal``.

Both variants share ``optimization_input``, ``rim_competition_pool`` (array),
``rim_competition_genome`` (object), ``fixture_id``, ``schema_version``.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CURRENT_OPTIMIZATION_FIXTURE_SCHEMA_VERSION: int = 1

_ALLOWED_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "fixture_id",
        "optimization_input",
        "primary_route_goal",
        "route_goals",
        "rim_competition_pool",
        "rim_competition_genome",
    }
)

_REQUIRED_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "fixture_id",
        "optimization_input",
        "rim_competition_pool",
        "rim_competition_genome",
    }
)


class OptimizationFixtureJsonError(ValueError):
    """Golden optimization fixture JSON violated the versioned contract."""


@dataclass(frozen=True)
class OptimizationFixtureJson:
    """Parsed v0 narrow-corridor optimization fixture (JSON-safe values only)."""

    schema_version: int
    fixture_id: str
    optimization_input: Mapping[str, object]
    primary_route_goal: Mapping[str, object] | None
    route_goals: Sequence[object] | None
    rim_competition_pool: Sequence[object]
    rim_competition_genome: Mapping[str, object]


def load_optimization_fixture_json(path: Path) -> OptimizationFixtureJson:
    if not path.is_file():
        msg = f"fixture path is not a file: {path}"
        raise OptimizationFixtureJsonError(msg)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return parse_optimization_fixture_json(raw)


def _validate_top_level_keys(data: dict[str, object]) -> None:
    keys = frozenset(data)
    unknown = keys - _ALLOWED_TOP_LEVEL_KEYS
    if unknown:
        msg = f"unknown top-level keys (policy: reject): {sorted(unknown)}"
        raise OptimizationFixtureJsonError(msg)
    missing = _REQUIRED_TOP_LEVEL_KEYS - keys
    if missing:
        msg = f"missing required top-level keys: {sorted(missing)}"
        raise OptimizationFixtureJsonError(msg)


def _validate_goal_export_shape(data: dict[str, object]) -> bool:
    has_primary = "primary_route_goal" in data
    has_route_goals = "route_goals" in data
    if has_primary == has_route_goals:
        msg = (
            "exactly one of primary_route_goal (asymmetric) or route_goals (symmetric) "
            "must be present at top level"
        )
        raise OptimizationFixtureJsonError(msg)
    return has_primary


def _require_schema_version(schema_raw: object) -> int:
    if type(schema_raw) is not int:
        msg = f"schema_version must be int, got {type(schema_raw).__name__}"
        raise OptimizationFixtureJsonError(msg)
    if schema_raw != CURRENT_OPTIMIZATION_FIXTURE_SCHEMA_VERSION:
        msg = (
            f"unsupported schema_version {schema_raw!r}; "
            f"only {CURRENT_OPTIMIZATION_FIXTURE_SCHEMA_VERSION} is accepted"
        )
        raise OptimizationFixtureJsonError(msg)
    return schema_raw


def _parse_goal_exports(
    data: dict[str, object], *, has_primary: bool
) -> tuple[dict[str, object] | None, list[object] | None]:
    if has_primary:
        prg = data["primary_route_goal"]
        if not isinstance(prg, dict):
            msg = f"primary_route_goal must be object, got {type(prg).__name__}"
            raise OptimizationFixtureJsonError(msg)
        return prg, None
    rg = data["route_goals"]
    if not isinstance(rg, list):
        msg = f"route_goals must be array, got {type(rg).__name__}"
        raise OptimizationFixtureJsonError(msg)
    return None, rg


def parse_optimization_fixture_json(data: Mapping[str, object]) -> OptimizationFixtureJson:
    if not isinstance(data, dict):
        msg = "root JSON value must be an object"
        raise OptimizationFixtureJsonError(msg)

    _validate_top_level_keys(data)
    has_primary = _validate_goal_export_shape(data)
    schema_raw = _require_schema_version(data["schema_version"])

    fixture_id = data["fixture_id"]
    if not isinstance(fixture_id, str) or not fixture_id.strip():
        msg = "fixture_id must be a non-empty string"
        raise OptimizationFixtureJsonError(msg)

    opt_in = data["optimization_input"]
    if not isinstance(opt_in, dict):
        msg = f"optimization_input must be object, got {type(opt_in).__name__}"
        raise OptimizationFixtureJsonError(msg)

    pool = data["rim_competition_pool"]
    if not isinstance(pool, list):
        msg = f"rim_competition_pool must be array, got {type(pool).__name__}"
        raise OptimizationFixtureJsonError(msg)

    genome = data["rim_competition_genome"]
    if not isinstance(genome, dict):
        msg = f"rim_competition_genome must be object, got {type(genome).__name__}"
        raise OptimizationFixtureJsonError(msg)

    primary, routes = _parse_goal_exports(data, has_primary=has_primary)

    return OptimizationFixtureJson(
        schema_version=schema_raw,
        fixture_id=fixture_id,
        optimization_input=copy.deepcopy(opt_in),
        primary_route_goal=copy.deepcopy(primary) if primary is not None else None,
        route_goals=copy.deepcopy(routes) if routes is not None else None,
        rim_competition_pool=copy.deepcopy(pool),
        rim_competition_genome=copy.deepcopy(genome),
    )


def optimization_fixture_json_to_safe_dict(fixture: OptimizationFixtureJson) -> dict[str, Any]:
    """Rebuild a plain ``dict`` tree suitable for JSON and builder equality checks."""

    out: dict[str, Any] = {
        "schema_version": fixture.schema_version,
        "fixture_id": fixture.fixture_id,
        "optimization_input": copy.deepcopy(dict(fixture.optimization_input)),
        "rim_competition_pool": copy.deepcopy(list(fixture.rim_competition_pool)),
        "rim_competition_genome": copy.deepcopy(dict(fixture.rim_competition_genome)),
    }
    if fixture.primary_route_goal is not None:
        out["primary_route_goal"] = copy.deepcopy(dict(fixture.primary_route_goal))
    if fixture.route_goals is not None:
        out["route_goals"] = copy.deepcopy(list(fixture.route_goals))
    return out
