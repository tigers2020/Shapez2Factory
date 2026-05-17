"""Golden JSON for narrow-corridor optimization DTOs (``json_safe_replay_value`` schema).

Artifacts: ``tests/fixtures/shapez_asteroid/optimization/narrow_corridor_*_rim_competition.json``.
Each file must match the Python builders in ``fixtures/narrow_corridor.py``. There is no
production deserialize; if builders change, regenerate the two ``.json`` files from
the same objects as :func:`_expected_asymmetric` / :func:`_expected_symmetric` (dump with
``json.dumps(..., sort_keys=True, indent=2)``).
"""

from __future__ import annotations

import json
from pathlib import Path

from django_apps.shapez_asteroid.optimization.optimization_replay import json_safe_replay_value
from tests.unit.shapez_asteroid.fixtures.narrow_corridor import (
    build_narrow_bridge_optimization_input,
    build_rim_competition_pool,
    build_symmetric_narrow_bridge_optimization_input,
    build_symmetric_rim_competition_pool,
)

_FIX_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "shapez_asteroid" / "optimization"


def _load_json(name: str) -> object:
    path = _FIX_DIR / name
    assert path.is_file(), path
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_asymmetric() -> dict[str, object]:
    inp, goal = build_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_rim_competition_pool(inp)
    return {
        "schema_version": 1,
        "fixture_id": "narrow_corridor_asymmetric_rim_competition_v0",
        "optimization_input": json_safe_replay_value(inp),
        "primary_route_goal": json_safe_replay_value(goal),
        "rim_competition_pool": json_safe_replay_value(pool),
        "rim_competition_genome": json_safe_replay_value(genome),
    }


def _expected_symmetric() -> dict[str, object]:
    inp, goals = build_symmetric_narrow_bridge_optimization_input(protected_bridge=True)
    pool, genome = build_symmetric_rim_competition_pool(inp)
    return {
        "schema_version": 1,
        "fixture_id": "narrow_corridor_symmetric_rim_competition_v0",
        "optimization_input": json_safe_replay_value(inp),
        "route_goals": json_safe_replay_value(goals),
        "rim_competition_pool": json_safe_replay_value(pool),
        "rim_competition_genome": json_safe_replay_value(genome),
    }


def test_narrow_corridor_asymmetric_json_fixture_matches_builder() -> None:
    assert _load_json("narrow_corridor_asymmetric_rim_competition.json") == _expected_asymmetric()


def test_narrow_corridor_symmetric_json_fixture_matches_builder() -> None:
    assert _load_json("narrow_corridor_symmetric_rim_competition.json") == _expected_symmetric()
