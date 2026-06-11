"""Diagnostics for trunk-first weighted rip-up inner fill."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TrunkFirstInnerFillDiagnostics:
    trunk_path_count: int = 0
    trunk_connected_miner_count: int = 0
    ripup_event_count: int = 0
    removed_miner_count: int = 0
    removed_extension_count: int = 0
    orphan_extension_pruned_count: int = 0
    failed_belt_route_count: int = 0
    failed_miner_attach_count: int = 0
    final_connected_miner_count: int = 0
    final_orphan_extension_count: int = 0

    def as_metrics_dict(self) -> dict[str, int]:
        return {
            "trunk_path_count": self.trunk_path_count,
            "trunk_connected_miner_count": self.trunk_connected_miner_count,
            "ripup_event_count": self.ripup_event_count,
            "removed_miner_count": self.removed_miner_count,
            "removed_extension_count": self.removed_extension_count,
            "orphan_extension_pruned_count": self.orphan_extension_pruned_count,
            "failed_belt_route_count": self.failed_belt_route_count,
            "failed_miner_attach_count": self.failed_miner_attach_count,
            "final_connected_miner_count": self.final_connected_miner_count,
            "final_orphan_extension_count": self.final_orphan_extension_count,
        }


__all__ = ["TrunkFirstInnerFillDiagnostics"]
