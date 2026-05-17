"""Contract tests for long stitched replay-track fixtures under ``replay_long/``."""

from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path

import pytest

from tests.unit.shapez_asteroid.fixtures.replay_json import (
    ReplayFixtureJsonError,
    load_replay_fixture_json,
    parse_replay_fixture_json,
    replay_fixture_json_to_safe_dict,
)

_FIX_LONG_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "shapez_asteroid" / "replay_long"
_EVOLUTION_COMMIT = _FIX_LONG_DIR / "narrow_corridor_evolution_commit_replay.json"
_TRUNCATED = _FIX_LONG_DIR / "narrow_corridor_truncated_replay.json"


@pytest.mark.parametrize("fixture_path", [_EVOLUTION_COMMIT, _TRUNCATED])
def test_long_replay_roundtrip(fixture_path: Path) -> None:
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    fixture = load_replay_fixture_json(fixture_path)
    assert replay_fixture_json_to_safe_dict(fixture) == raw
    if fixture_path == _EVOLUTION_COMMIT:
        assert fixture.truncation_reason is None
    else:
        assert fixture.truncation_reason == "recording_frame_budget"


def test_long_replay_event_ordering() -> None:
    fixture = load_replay_fixture_json(_EVOLUTION_COMMIT)
    seq = list(fixture.replay_event_sequence)
    assert seq[0] == "optimization.input_loaded"
    last_generation_completed = max(i for i, e in enumerate(seq) if e == "generation.completed")
    first_best = seq.index("best_genome.selected")
    first_route_attempt = seq.index("route.commit_attempted")
    assert last_generation_completed < first_best < first_route_attempt


def test_best_genome_precedes_commit_phase() -> None:
    fixture = load_replay_fixture_json(_EVOLUTION_COMMIT)
    seq = list(fixture.replay_event_sequence)
    assert seq.index("best_genome.selected") < seq.index("route.commit_attempted")


def test_final_event_is_survivability_summary() -> None:
    fixture = load_replay_fixture_json(_EVOLUTION_COMMIT)
    assert fixture.replay_event_sequence[-1] == "commit.survivability_summary"


def test_truncated_replay_contract() -> None:
    fixture = load_replay_fixture_json(_TRUNCATED)
    assert fixture.replay_summary["replay_truncated"] is True
    assert fixture.truncation_reason == "recording_frame_budget"
    assert "commit.survivability_summary" not in fixture.replay_event_sequence
    assert fixture.replay_event_sequence[-1] == "generation.completed"


def test_truncation_boundary_is_deterministic() -> None:
    full_raw = json.loads(_EVOLUTION_COMMIT.read_text(encoding="utf-8"))
    trunc_raw = json.loads(_TRUNCATED.read_text(encoding="utf-8"))
    n = len(trunc_raw["replay_frames"])
    assert full_raw["replay_frames"][:n] == trunc_raw["replay_frames"]


def test_replay_summary_counts_match_frames() -> None:
    for path in (_EVOLUTION_COMMIT, _TRUNCATED):
        fixture = load_replay_fixture_json(path)
        seq = list(fixture.replay_event_sequence)
        expected = dict(sorted(Counter(seq).items()))
        assert fixture.replay_summary["event_type_counts"] == expected
        assert fixture.replay_summary["frame_count"] == len(seq) == len(fixture.replay_frames)


def test_long_replay_parser_rejects_invalid_summary() -> None:
    raw: dict[str, object] = json.loads(_EVOLUTION_COMMIT.read_text(encoding="utf-8"))
    summary = dict(raw["replay_summary"])
    summary["event_type_counts"] = {"commit.survivability_summary": 1}
    raw["replay_summary"] = summary
    with pytest.raises(ReplayFixtureJsonError, match="event_type_counts"):
        parse_replay_fixture_json(raw)


def test_truncation_reason_rejected_when_not_truncated() -> None:
    raw: dict[str, object] = json.loads(_EVOLUTION_COMMIT.read_text(encoding="utf-8"))
    raw["truncation_reason"] = "should_not_be_here"
    with pytest.raises(ReplayFixtureJsonError, match="truncation_reason must be absent"):
        parse_replay_fixture_json(raw)


def test_truncation_reason_required_when_truncated() -> None:
    raw: dict[str, object] = json.loads(_TRUNCATED.read_text(encoding="utf-8"))
    del raw["truncation_reason"]
    with pytest.raises(ReplayFixtureJsonError, match="truncation_reason is required"):
        parse_replay_fixture_json(raw)


def test_long_replay_remains_output_only() -> None:
    import tests.unit.shapez_asteroid.test_long_replay_fixture_contract as mod

    tree = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("django_apps"), node.module

    import tests.unit.shapez_asteroid.fixtures.replay_json as replay_json

    src = Path(replay_json.__file__).read_text(encoding="utf-8")
    assert "commit_best_genome" not in src
    assert "run_evolutionary_search" not in src
