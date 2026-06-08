"""Committed large fluid map fixtures for L3 route probe budget regression (PR-1)."""

from __future__ import annotations

import json
from pathlib import Path

from shapez2_factory.adapters.asteroid_lab.complete_map_serializer import parse_complete_map
from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.adapters.asteroid_lab.json_snapshot_rules import (
    JsonSnapshotGameDataRulesAdapter,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap

_FIXTURE_ROOT = Path(__file__).resolve().parents[4] / "fixtures" / "asteroid_lab" / "large_fluid_map"


def large_fluid_map_fixture_dir() -> Path:
    return _FIXTURE_ROOT


def load_large_fluid_complete_map() -> ReconstructionCompleteMap:
    payload = json.loads((_FIXTURE_ROOT / "complete_map.json").read_text(encoding="utf-8"))
    return parse_complete_map(payload)


def load_large_fluid_genetic_sample_seeds() -> GeneticSampleSeedSnapshot:
    payload = json.loads((_FIXTURE_ROOT / "genetic_sample_seeds.json").read_text(encoding="utf-8"))
    return GeneticSampleSeedSnapshot.from_payload(payload)


def load_large_fluid_game_data_rules() -> JsonSnapshotGameDataRulesAdapter:
    payload = json.loads((_FIXTURE_ROOT / "game_data_snapshot.json").read_text(encoding="utf-8"))
    return JsonSnapshotGameDataRulesAdapter.from_payload(payload)
