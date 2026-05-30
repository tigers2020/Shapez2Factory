"""Shim: relocated to core ``game_data_snapshot_provenance`` (PR-CLI-2a).

Core module: ``shapez2_factory.domain.asteroid_lab.game_data_snapshot_provenance``.
Re-exports the pure core provenance DTOs so existing ``django_apps`` imports keep working.
Import the core module directly in new code.
"""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.game_data_snapshot_provenance import (
    GameDataSnapshotProvenance,
    ProvenanceParseError,
    ProvenanceParseErrorCode,
    parse_provenance_config,
    parse_provenance_config_latest,
    parse_provenance_config_v1,
    provenance_from_snapshot,
    provenance_stub_diagnostic_dict,
    provenance_to_config_dict,
)

__all__ = [
    "GameDataSnapshotProvenance",
    "ProvenanceParseError",
    "ProvenanceParseErrorCode",
    "parse_provenance_config",
    "parse_provenance_config_latest",
    "parse_provenance_config_v1",
    "provenance_from_snapshot",
    "provenance_stub_diagnostic_dict",
    "provenance_to_config_dict",
]
