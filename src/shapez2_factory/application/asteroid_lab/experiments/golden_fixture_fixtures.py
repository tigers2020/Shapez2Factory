"""Django-free helpers to load asteroid_golden frozen fixtures (PR-2)."""

from __future__ import annotations

import json
from pathlib import Path

from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.adapters.asteroid_lab.json_snapshot_rules import (
    JsonSnapshotGameDataRulesAdapter,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_loader import (
    load_shapez_copy_string,
)

_FIXTURE_ROOT = Path(__file__).resolve().parents[5] / "tests" / "fixtures" / "asteroid_golden"


def golden_fixture_dir() -> Path:
    return _FIXTURE_ROOT


def load_empty_copy() -> str:
    return load_shapez_copy_string(_FIXTURE_ROOT / "empty.shapez.txt")


def load_golden_copy() -> str:
    return load_shapez_copy_string(_FIXTURE_ROOT / "golden.shapez.txt")


def load_game_data_rules() -> JsonSnapshotGameDataRulesAdapter:
    payload = json.loads(
        (_FIXTURE_ROOT / "game_data_snapshot_min.json").read_text(encoding="utf-8"),
    )
    return JsonSnapshotGameDataRulesAdapter.from_payload(payload)


def load_genetic_sample_seeds() -> GeneticSampleSeedSnapshot:
    payload = json.loads(
        (_FIXTURE_ROOT / "genetic_sample_seeds.json").read_text(encoding="utf-8"),
    )
    return GeneticSampleSeedSnapshot.from_payload(payload)


def load_genetic_sample_seeds_payload() -> dict[str, object]:
    payload: dict[str, object] = json.loads(
        (_FIXTURE_ROOT / "genetic_sample_seeds.json").read_text(encoding="utf-8"),
    )
    return payload


__all__ = [
    "golden_fixture_dir",
    "load_empty_copy",
    "load_game_data_rules",
    "load_genetic_sample_seeds",
    "load_genetic_sample_seeds_payload",
    "load_golden_copy",
]
