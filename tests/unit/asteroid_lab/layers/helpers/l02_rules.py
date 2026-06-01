"""Layer 02 rules fixtures."""

from pathlib import Path

from shapez2_factory.adapters.asteroid_lab.json_snapshot_rules import (
    JsonSnapshotGameDataRulesAdapter,
)

_SNAPSHOT_FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "fixtures"
    / "asteroid_lab"
    / "game_data_snapshot_min.json"
)


def snapshot_rules_for_test() -> JsonSnapshotGameDataRulesAdapter:
    """Load the minimal game-data snapshot rules for Layer 02 core tests."""
    return JsonSnapshotGameDataRulesAdapter.from_file(_SNAPSHOT_FIXTURE)
