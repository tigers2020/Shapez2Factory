"""Contract tests for :mod:`tests.unit.shapez_asteroid.fixtures.replay_json`."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from tests.unit.shapez_asteroid.fixtures.replay_json import (
    CURRENT_REPLAY_FIXTURE_SCHEMA_VERSION,
    ReplayFixtureJsonError,
    load_replay_fixture_json,
    parse_replay_fixture_json,
    replay_fixture_json_to_safe_dict,
)
from tests.unit.shapez_asteroid.fixtures.replay_track_builders import (
    expected_narrow_corridor_asymmetric_replay_fixture_v0,
    expected_narrow_corridor_starvation_replay_fixture_v0,
    expected_narrow_corridor_symmetric_replay_fixture_v0,
)

_FIX_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "shapez_asteroid" / "replay"


def test_asymmetric_replay_fixture_roundtrip() -> None:
    path = _FIX_DIR / "narrow_corridor_asymmetric_replay.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    fixture = load_replay_fixture_json(path)
    safe = replay_fixture_json_to_safe_dict(fixture)
    assert safe == raw
    assert safe == expected_narrow_corridor_asymmetric_replay_fixture_v0()


def test_symmetric_replay_fixture_roundtrip() -> None:
    path = _FIX_DIR / "narrow_corridor_symmetric_replay.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    fixture = load_replay_fixture_json(path)
    safe = replay_fixture_json_to_safe_dict(fixture)
    assert safe == raw
    assert safe == expected_narrow_corridor_symmetric_replay_fixture_v0()


def test_starvation_replay_fixture_roundtrip() -> None:
    path = _FIX_DIR / "narrow_corridor_starvation_replay.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    fixture = load_replay_fixture_json(path)
    safe = replay_fixture_json_to_safe_dict(fixture)
    assert safe == raw
    assert safe == expected_narrow_corridor_starvation_replay_fixture_v0()


def test_replay_event_sequence_matches_expected_subsequence() -> None:
    path = _FIX_DIR / "narrow_corridor_asymmetric_replay.json"
    fixture = load_replay_fixture_json(path)
    seq = list(fixture.replay_event_sequence)
    first_attempt = seq.index("route.commit_attempted")
    first_commit = seq.index("route.committed")
    second_attempt = seq.index("route.commit_attempted", first_attempt + 1)
    rollback = seq.index("route.rolled_back")
    summary = seq.index("commit.survivability_summary")
    assert first_attempt < first_commit < second_attempt < rollback < summary


def test_replay_summary_metrics_are_deterministic() -> None:
    path = _FIX_DIR / "narrow_corridor_symmetric_replay.json"
    fixture = load_replay_fixture_json(path)
    summary = dict(fixture.replay_summary)
    assert summary["frame_count"] == len(fixture.replay_frames)
    assert summary["replay_truncated"] is False
    assert summary["event_type_counts"] == {
        "commit.survivability_summary": 1,
        "route.commit_attempted": 2,
        "route.committed": 1,
        "route.rolled_back": 1,
    }


def test_replay_fixture_rejects_unknown_schema_version() -> None:
    data = dict(expected_narrow_corridor_asymmetric_replay_fixture_v0())
    data["schema_version"] = CURRENT_REPLAY_FIXTURE_SCHEMA_VERSION + 1
    with pytest.raises(ReplayFixtureJsonError, match="unsupported schema_version"):
        parse_replay_fixture_json(data)


def test_replay_fixture_rejects_unknown_top_level_keys() -> None:
    data = dict(expected_narrow_corridor_asymmetric_replay_fixture_v0())
    data["extra_top"] = 1
    with pytest.raises(ReplayFixtureJsonError, match="unknown top-level"):
        parse_replay_fixture_json(data)


def test_replay_fixture_parser_has_no_django_apps_imports() -> None:
    import tests.unit.shapez_asteroid.fixtures.replay_json as replay_json

    tree = ast.parse(Path(replay_json.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("django_apps"), node.module


def test_replay_fixture_contract_does_not_execute_solver() -> None:
    import tests.unit.shapez_asteroid.fixtures.replay_json as replay_json

    src = Path(replay_json.__file__).read_text(encoding="utf-8")
    assert "commit_best_genome" not in src
    assert "run_evolutionary_search" not in src
    assert "run_route_probe" not in src
